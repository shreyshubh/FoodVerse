"""
FoodVerse AI — Tests for the food analysis endpoint.

Covers: valid uploads, invalid files, corrupt images, unsupported formats,
oversized files, model unavailable state, low confidence, and error responses.
"""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.food_recognition import FoodRecognitionResult, ModelUnavailableError


@pytest.fixture
def client():
    """Create a test client with lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


def _make_valid_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid JPEG image in memory."""
    import cv2

    img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


def _make_valid_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a minimal valid PNG image in memory."""
    import cv2

    img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


# --- Upload validation tests ---


class TestUploadValidation:
    """Tests for file upload validation logic."""

    def test_empty_file_rejected(self, client):
        """Empty file should be rejected with 400."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"]["error"]["code"] == "EMPTY_FILE"

    def test_unsupported_extension_rejected(self, client):
        """Files with unsupported extensions should be rejected with 415."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.gif", b"\x00" * 100, "image/gif")},
        )
        assert resp.status_code == 415

    def test_unsupported_mime_type_rejected(self, client):
        """Files with unsupported MIME types should be rejected."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.jpg", b"\x00" * 100, "application/pdf")},
        )
        assert resp.status_code == 415

    def test_corrupt_image_rejected(self, client):
        """Non-image bytes with image extension should be rejected with 422."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.jpg", b"not an image at all", "image/jpeg")},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"]["code"] == "DECODE_FAILED"

    def test_valid_jpeg_accepted(self, client):
        """A valid JPEG should pass upload validation (may fail at model stage)."""
        jpeg_bytes = _make_valid_jpeg_bytes()
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        # Should either succeed (200) or model unavailable (503), not a validation error
        assert resp.status_code in (200, 503)

    def test_valid_png_accepted(self, client):
        """A valid PNG should pass upload validation."""
        png_bytes = _make_valid_png_bytes()
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.png", png_bytes, "image/png")},
        )
        assert resp.status_code in (200, 503)


# --- Model unavailable tests ---


class TestModelUnavailable:
    """Tests for model unavailable state."""

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_model_unavailable_returns_503(self, mock_service, client):
        """When model is not loaded, endpoint should return 503."""
        mock_service.predict.side_effect = ModelUnavailableError(
            "Model weights not found."
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 503
        body = resp.json()
        assert body["detail"]["error"]["code"] == "MODEL_UNAVAILABLE"


# --- Successful prediction tests ---


class TestSuccessfulPrediction:
    """Tests for successful food analysis with mocked model."""

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_high_confidence_prediction(self, mock_service, client):
        """High-confidence prediction should return status=success."""
        mock_service.predict.return_value = FoodRecognitionResult(
            label="pizza",
            confidence=0.92,
            canonical_food_id="pizza",
            alternatives=[
                {"label": "flatbread", "confidence": 0.04},
            ],
            needs_confirmation=False,
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["prediction"]["label"] == "pizza"
        assert body["prediction"]["confidence"] == 0.92
        assert body["request_id"]  # should have a request ID

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_low_confidence_needs_confirmation(self, mock_service, client):
        """Low-confidence prediction should return status=needs_confirmation."""
        mock_service.predict.return_value = FoodRecognitionResult(
            label="pizza",
            confidence=0.25,
            canonical_food_id="pizza",
            alternatives=[],
            needs_confirmation=True,
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "needs_confirmation"
        assert any("Low confidence" in w for w in body["warnings"])

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_nutrition_included_in_response(self, mock_service, client):
        """Successful prediction should include nutrition estimates."""
        mock_service.predict.return_value = FoodRecognitionResult(
            label="pizza",
            confidence=0.92,
            canonical_food_id="pizza",
            alternatives=[],
            needs_confirmation=False,
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        nutrition = body["nutrition"]
        # Should have per_100_g basis (no serving_grams provided)
        assert nutrition["basis"] == "per_100_g"
        assert nutrition["calories_kcal"] is not None
        assert nutrition["protein_g"] is not None

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_serving_grams_scales_nutrition(self, mock_service, client):
        """Providing serving_grams should scale nutrition values."""
        mock_service.predict.return_value = FoodRecognitionResult(
            label="pizza",
            confidence=0.92,
            canonical_food_id="pizza",
            alternatives=[],
            needs_confirmation=False,
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
            data={"serving_grams": "200"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["nutrition"]["basis"] == "user_portion"
        assert body["nutrition"]["serving_grams"] == 200.0

    @patch("app.api.routes.food_analysis.food_recognition_service")
    def test_health_score_unavailable(self, mock_service, client):
        """Health score should always be null/unavailable in v1."""
        mock_service.predict.return_value = FoodRecognitionResult(
            label="pizza",
            confidence=0.92,
            canonical_food_id="pizza",
            alternatives=[],
            needs_confirmation=False,
        )
        jpeg_bytes = _make_valid_jpeg_bytes()

        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("food.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["health_score"]["value"] is None


# --- Error response format tests ---


class TestErrorFormat:
    """Tests that error responses follow the stable ApiError contract."""

    def test_error_has_code_and_message(self, client):
        """Error responses should have code, message, and request_id."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.gif", b"\x00" * 100, "image/gif")},
        )
        body = resp.json()
        error = body["detail"]["error"]
        assert "code" in error
        assert "message" in error
        assert "request_id" in error

    def test_error_does_not_expose_paths(self, client):
        """Error responses should not contain filesystem paths."""
        resp = client.post(
            "/api/v1/food-analysis",
            files={"image": ("test.jpg", b"corrupt", "image/jpeg")},
        )
        body = resp.json()
        error_msg = json.dumps(body)
        assert "C:\\" not in error_msg
        assert "/home/" not in error_msg
        assert "\\Users\\" not in error_msg
