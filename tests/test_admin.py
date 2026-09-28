from fastapi.testclient import TestClient

from app import auth, db
from app.main import app


def client_without_database(monkeypatch):
    monkeypatch.setattr(db, "initialize_database", lambda: None)
    return TestClient(app)


def test_admin_requires_login_and_csrf(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "negocio")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", auth.make_password_hash("clave-de-prueba"))
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setattr(db, "list_admin_products", lambda: [])
    with client_without_database(monkeypatch) as client:
        assert client.get("/admin", follow_redirects=False).headers["location"] == "/admin/login"
        assert client.get("/api/admin/products").status_code == 401
        assert client.post("/api/admin/login", json={"username": "negocio", "password": "mal"}).status_code == 401
        assert client.post("/api/admin/login", json={"username": "negocio", "password": "clave-de-prueba"}).status_code == 200
        assert client.get("/admin").status_code == 200
        token = client.get("/api/admin/session").json()["csrf_token"]
        assert client.post("/api/admin/products", json={"name": "Pizza", "price_cents": 500}).status_code == 403
        assert client.post("/api/admin/logout", headers={"X-CSRF-Token": token}).status_code == 200
        assert client.get("/api/admin/products").status_code == 401


def test_product_creation_and_update_are_protected(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "negocio")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", auth.make_password_hash("clave-de-prueba"))
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    saved = {}

    def create(data):
        saved.update({"id": 7, **data})
        return saved.copy()

    def update(product_id, data):
        assert product_id == 7
        saved.update(data)
        return saved.copy()

    monkeypatch.setattr(db, "create_product", create)
    monkeypatch.setattr(db, "update_product", update)
    monkeypatch.setattr(db, "list_admin_products", lambda: [saved.copy()] if saved else [])
    with client_without_database(monkeypatch) as client:
        client.post("/api/admin/login", json={"username": "negocio", "password": "clave-de-prueba"})
        token = client.get("/api/admin/session").json()["csrf_token"]
        headers = {"X-CSRF-Token": token}
        product = {"name": "Pizza", "price_cents": 1200000, "is_published": True}
        assert client.post("/api/admin/products", json=product, headers=headers).status_code == 201
        assert client.get("/api/admin/products").json()[0]["name"] == "Pizza"
        product["is_available"] = False
        assert client.put("/api/admin/products/7", json=product, headers=headers).json()["is_available"] is False
        assert client.post("/api/admin/products", json={"name": " ", "price_cents": 10}, headers=headers).status_code == 422
        assert client.post("/api/admin/products", json={"name": "X", "price_cents": 10, "image_url": "http://bad.test"}, headers=headers).status_code == 422
