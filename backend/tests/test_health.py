"""Health check and basic API tests."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body


def test_api_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200
