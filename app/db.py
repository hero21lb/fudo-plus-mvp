import os
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT NOT NULL DEFAULT '',
    image_url TEXT,
    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

DEMO_PRODUCTS = (
    ("Hamburguesa clásica", "Medallón de carne, queso, lechuga y tomate.", 850000),
    ("Pizza muzzarella", "Salsa de tomate, muzzarella y aceitunas.", 1200000),
    ("Limonada", "Limonada fresca de medio litro.", 320000),
)


def connect():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Falta DATABASE_URL")
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5)


def initialize_database():
    last_error = None
    for attempt in range(10):
        try:
            with connect() as connection:
                connection.execute(SCHEMA)
                connection.execute(Path(__file__).with_name("orders.sql").read_text(encoding="utf-8"))
                if os.getenv("SEED_DEMO_PRODUCTS", "false").lower() == "true":
                    count = connection.execute("SELECT count(*) AS total FROM products").fetchone()["total"]
                    if count == 0:
                        with connection.cursor() as cursor:
                            cursor.executemany(
                                """INSERT INTO products
                                (name, description, price_cents, is_published, is_available)
                                VALUES (%s, %s, %s, TRUE, TRUE)""",
                                DEMO_PRODUCTS,
                            )
            return
        except psycopg.OperationalError as error:
            last_error = error
            if attempt < 9:
                time.sleep(2)
    raise RuntimeError("No se pudo conectar a PostgreSQL") from last_error


def list_published_products():
    with connect() as connection:
        return connection.execute(
            """SELECT id, name, description, image_url, price_cents, is_available
            FROM products WHERE is_published = TRUE ORDER BY id"""
        ).fetchall()


def list_admin_products():
    with connect() as connection:
        return connection.execute(
            """SELECT id, name, description, image_url, price_cents,
            is_published, is_available FROM products ORDER BY id DESC"""
        ).fetchall()


def create_product(data: dict):
    with connect() as connection:
        return connection.execute(
            """INSERT INTO products
            (name, description, image_url, price_cents, is_published, is_available)
            VALUES (%(name)s, %(description)s, %(image_url)s, %(price_cents)s,
                    %(is_published)s, %(is_available)s)
            RETURNING id, name, description, image_url, price_cents,
                      is_published, is_available""",
            data,
        ).fetchone()


def update_product(product_id: int, data: dict):
    with connect() as connection:
        return connection.execute(
            """UPDATE products SET name = %(name)s, description = %(description)s,
            image_url = %(image_url)s, price_cents = %(price_cents)s,
            is_published = %(is_published)s, is_available = %(is_available)s
            WHERE id = %(id)s
            RETURNING id, name, description, image_url, price_cents,
                      is_published, is_available""",
            {**data, "id": product_id},
        ).fetchone()


def database_is_ready():
    with connect() as connection:
        connection.execute("SELECT 1")


def create_order(data: dict):
    # The connection context commits everything together or rolls it all back.
    with connect() as connection:
        ids = [item["product_id"] for item in data["items"]]
        products = connection.execute(
            "SELECT id, name, price_cents FROM products WHERE id = ANY(%s) "
            "AND is_published AND is_available ORDER BY id FOR SHARE", (ids,),
        ).fetchall()
        by_id = {product["id"]: product for product in products}
        if len(by_id) != len(ids):
            raise ValueError("Un producto ya no está disponible. Actualizá el menú y revisá tu pedido.")
        total = sum(by_id[item["product_id"]]["price_cents"] * item["quantity"] for item in data["items"])
        # Guests use the order snapshot; no account or customer identity is inferred from a phone.
        order = connection.execute(
            """INSERT INTO orders (customer_name, customer_phone, fulfillment_method,
            delivery_address, delivery_reference, total_cents, payment_method, payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, status, total_cents, payment_method, payment_status, created_at""",
            (data["customer_name"], data["customer_phone"], data["fulfillment_method"],
             data["delivery_address"], data["delivery_reference"], total,
             data["payment_method"], "simulated" if data["payment_method"] == "simulated" else "pending"),
        ).fetchone()
        with connection.cursor() as cursor:
            cursor.executemany(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price_cents)
                VALUES (%s, %s, %s, %s, %s)""",
                [(order["id"], item["product_id"], by_id[item["product_id"]]["name"],
                  item["quantity"], by_id[item["product_id"]]["price_cents"]) for item in data["items"]],
            )
        return order


def list_orders():
    with connect() as connection:
        orders = connection.execute("SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT 100").fetchall()
        if orders:
            items = connection.execute(
                "SELECT * FROM order_items WHERE order_id = ANY(%s) ORDER BY id",
                ([order["id"] for order in orders],),
            ).fetchall()
            grouped = {}
            for item in items:
                grouped.setdefault(item["order_id"], []).append(item)
            for order in orders:
                order["items"] = grouped.get(order["id"], [])
        return orders
