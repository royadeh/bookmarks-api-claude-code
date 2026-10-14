from fastapi.testclient import TestClient

from app.main import app, create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_level_app_serves_health() -> None:
    client = TestClient(app)

    assert client.get("/health").status_code == 200
