import os
import time

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
