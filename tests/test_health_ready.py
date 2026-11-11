"""Tests for health, readiness, and metrics endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test that /health returns liveness status, version, and commit."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "commit" in data


def test_readiness_healthy(client: TestClient) -> None:
    """Test that /ready returns 200 when database connectivity is healthy."""
    with patch("app.main.check_db_connection", return_value=True):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


def test_readiness_database_failure(client: TestClient) -> None:
    """Test that /ready returns 503 when database connectivity is lost."""
    with patch("app.main.check_db_connection", return_value=False):
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert "unhealthy" in str(data)


def test_metrics_endpoint(client: TestClient) -> None:
    """Test that Prometheus /metrics returns scrapable metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests" in response.text or "python_info" in response.text
