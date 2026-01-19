"""Test suite for API health endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_live(client):
    """Test liveness probe endpoint."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_health_ready_no_mongo(client):
    """Test readiness probe without MongoDB connection."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_health_endpoint_structure(client):
    """Test health endpoint returns proper structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "checks" in data
