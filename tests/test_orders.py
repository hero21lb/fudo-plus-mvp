import pytest
from fastapi.testclient import TestClient

from app import auth, db
from app.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(db, "initialize_database", lambda: None)
    with TestClient(app) as client:
        yield client


def payload(**changes):
    return {"customer_name": " Ana ", "customer_phone": " 123 ",
            "fulfillment_method": "pickup", "items": [{"product_id": 1, "quantity": 2}], **changes}


@pytest.mark.parametrize("changes", [
    {"customer_name": " "}, {"customer_phone": " "}, {"items": []},
    {"items": [{"product_id": 1, "quantity": 0}]},
    {"items": [{"product_id": 1, "quantity": 2}, {"product_id": 1, "quantity": 1}]},
    {"fulfillment_method": "delivery", "delivery_address": " "},
    {"payment_method": "online"}, {"payment_status": "approved"}, {"total_cents": 1},
    {"items": [{"product_id": 1, "quantity": 1, "unit_price_cents": 1}]},
])
def test_invalid_orders_never_reach_database(client, monkeypatch, changes):
    def unexpected(_):
        pytest.fail("Invalid request reached database")
    monkeypatch.setattr(db, "create_order", unexpected)
    assert client.post("/api/orders", json=payload(**changes)).status_code == 422


def test_guest_order_normalizes_contact_and_clears_pickup_address(client, monkeypatch):
    saved = {}
    def create(data):
        saved.update(data)
        return {"id": 4, "total_cents": 2000, "payment_status": "pending"}
    monkeypatch.setattr(db, "create_order", create)
    result = client.post("/api/orders", json=payload(delivery_address="Old address"))
    assert result.status_code == 201
    assert saved["customer_name"] == "Ana"
    assert saved["customer_phone"] == "123"
    assert saved["delivery_address"] is None
    assert result.json()["total_cents"] == 2000


def test_unavailable_product_reports_conflict(client, monkeypatch):
    def unavailable(_):
        raise ValueError("Producto agotado")
    monkeypatch.setattr(db, "create_order", unavailable)
    assert client.post("/api/orders", json=payload()).status_code == 409


def test_database_failure_is_reported_without_details(client, monkeypatch):
    def broken(_):
        raise RuntimeError("private connection details")
    monkeypatch.setattr(db, "create_order", broken)
    response = client.post("/api/orders", json=payload())
    assert response.status_code == 503
    assert "private" not in response.text


def test_tickets_require_admin(client, monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("ADMIN_USERNAME", "negocio")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", auth.make_password_hash("test-password"))
    monkeypatch.setattr(db, "list_orders", lambda: [{"id": 2, "items": []}])
    assert client.get("/api/admin/orders").status_code == 401
    client.post("/api/admin/login", json={"username": "negocio", "password": "test-password"})
    assert client.get("/api/admin/orders").json() == [{"id": 2, "items": []}]


class RecordingConnection:
    def __init__(self, products, fail_items=False):
        self.products = products
        self.fail_items = fail_items
        self.calls = []
        self.exit_error = None

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        self.exit_error = error_type

    def execute(self, sql, values):
        self.calls.append((sql, values))
        return self

    def fetchall(self):
        return self.products

    def fetchone(self):
        return {"id": 42}

    def cursor(self):
        connection = self
        class Cursor:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def executemany(self, sql, values):
                if connection.fail_items:
                    raise RuntimeError("insert failed")
                connection.calls.append((sql, values))
        return Cursor()


@pytest.mark.parametrize("method, status", [("cash", "pending"), ("simulated", "simulated")])
def test_database_uses_current_price_and_product_snapshot(monkeypatch, method, status):
    connection = RecordingConnection([{"id": 1, "name": "Pizza actual", "price_cents": 1250}])
    monkeypatch.setattr(db, "connect", lambda: connection)
    data = payload(payment_method=method, delivery_address=None, delivery_reference=None)
    assert db.create_order(data)["id"] == 42
    order_values = connection.calls[1][1]
    assert order_values[5:] == (2500, method, status)
    assert connection.calls[2][1] == [(42, 1, "Pizza actual", 2, 1250)]


def test_missing_product_aborts_before_order_insert(monkeypatch):
    connection = RecordingConnection([])
    monkeypatch.setattr(db, "connect", lambda: connection)
    with pytest.raises(ValueError):
        db.create_order(payload())
    assert len(connection.calls) == 1
    assert connection.exit_error is ValueError


def test_item_failure_exits_transaction_with_error(monkeypatch):
    connection = RecordingConnection([{"id": 1, "name": "Pizza", "price_cents": 1250}], fail_items=True)
    monkeypatch.setattr(db, "connect", lambda: connection)
    with pytest.raises(RuntimeError):
        db.create_order(payload(delivery_address=None, delivery_reference=None, payment_method="cash"))
    assert connection.exit_error is RuntimeError
