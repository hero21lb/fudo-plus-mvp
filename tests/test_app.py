from fastapi.testclient import TestClient

from app import db
from app.main import app


def test_menu_lists_published_products(monkeypatch):
    monkeypatch.setattr(db, "initialize_database", lambda: None)
    monkeypatch.setattr(
        db,
        "list_published_products",
        lambda: [{
            "id": 1,
            "name": "Pizza",
            "description": "Muzzarella",
            "image_url": None,
            "price_cents": 1200000,
            "is_available": False,
        }],
    )
    with TestClient(app) as client:
        response = client.get("/api/products")
        assert response.status_code == 200
        assert response.json()[0]["is_available"] is False
        assert client.get("/").status_code == 200


def test_menu_reports_database_error(monkeypatch):
    monkeypatch.setattr(db, "initialize_database", lambda: None)
    monkeypatch.setattr(db, "list_published_products", lambda: (_ for _ in ()).throw(RuntimeError("DB missing")))
    with TestClient(app) as client:
        response = client.get("/api/products")
        assert response.status_code == 503
        assert "menú" in response.json()["detail"]


def test_ready_checks_database(monkeypatch):
    monkeypatch.setattr(db, "initialize_database", lambda: None)
    monkeypatch.setattr(db, "database_is_ready", lambda: None)
    with TestClient(app) as client:
        assert client.get("/ready").json() == {"status": "ok"}
