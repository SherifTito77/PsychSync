import pytest
from starlette.testclient import TestClient

from app.main import app as fastapi_app


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def route_exists(app, path: str) -> bool:
    return any(getattr(route, "path", None) == path for route in app.routes)


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_health_endpoint_if_registered(app, client):
    if not route_exists(app, "/api/v1/health"):
        pytest.skip("/api/v1/health is not registered on this app")

    response = client.get("/api/v1/health")
    assert response.status_code == 200
