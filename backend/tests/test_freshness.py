"""
FoodVerse AI — Freshness Detector Tests.
"""
import io
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def create_test_image_bytes():
    img = Image.new("RGB", (100, 100), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_freshness_offline_envelope(client):
    """When GROQ_API_KEY is unset, returns explicit provider_unavailable envelope, not fake banana."""
    img_bytes = create_test_image_bytes()
    resp = client.post(
        "/api/v1/freshness-analysis",
        files={"image": ("test.jpg", img_bytes, "image/jpeg")},
        data={"food_name": "Apple", "storage_type": "Countertop", "storage_days": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "request_id" in data
    assert data["food_name"] == "Apple"
    if data["status"] == "provider_unavailable":
        assert data["freshness_state"] == "Unverified"
        assert data["safety_status"] == "UNDETERMINED"
        assert "GROQ_API_KEY" in data["reasoning"]


def test_freshness_deterministic_safety_override(client):
    """When model reports SAFE but storage days exceed threshold, safety layer overrides to CAUTION."""
    from app.core.groq_provider import groq_provider

    mock_groq_response = {
        "detected_food": "Chicken Breast",
        "freshness_state": "Fresh",
        "safety_status": "SAFE",
        "confidence": 88.0,
        "observed_signs": ["Normal color"],
        "reasoning": "Looks fresh visually.",
        "advice": "Cook thoroughly.",
    }

    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "analyze_freshness", return_value=mock_groq_response):
        img_bytes = create_test_image_bytes()
        # Stored for 5 days at Room Temp (max safe is 2 days)
        resp = client.post(
            "/api/v1/freshness-analysis",
            files={"image": ("chicken.jpg", img_bytes, "image/jpeg")},
            data={"food_name": "Chicken Breast", "storage_type": "Room Temp", "storage_days": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        # Overridden to CAUTION due to high-risk room temp storage duration
        assert data["safety_status"] == "CAUTION"
        assert any("threshold" in s.lower() for s in data["signs"])


def test_freshness_empty_file_rejected(client):
    resp = client.post(
        "/api/v1/freshness-analysis",
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 400
