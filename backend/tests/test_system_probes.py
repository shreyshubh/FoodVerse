"""
FoodVerse AI — System Liveness & Deep Readiness Tests.
"""
import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_liveness_probe(client):
    """GET /health returns 200 and liveness status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "services" in data
    assert "groq_provider" in data["services"]
    assert "database" in data["services"]


def test_readiness_probe(client):
    """GET /ready returns deep status for local models, reference databases, and external providers."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"ready", "degraded"}
    assert "models" in data
    assert data["models"]["food_recognition"] == "loaded"
    assert data["models"]["nutrition_reference"] == "loaded"
    assert "external_providers" in data
    assert "database" in data
    assert "groq_ai" in data["external_providers"]
    assert "orchestration" in data
