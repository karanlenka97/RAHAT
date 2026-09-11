"""Tests for health check and root endpoints."""


def test_root_endpoint(client):
    """Verify that GET / returns status 200 and expected metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data
    assert data["health"] == "/health"


def test_health_check_endpoint(client):
    """Verify that GET /health returns status 200 and ok health status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rahat-backend"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data


def test_api_v1_health_endpoint(client):
    """Verify that GET /api/v1/health returns status 200 and ok health status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rahat-backend"
