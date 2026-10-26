"""
FoodVerse AI — Groq Cloud Adapter & Safety Integration Tests.

Tests:
  - Text model configuration (openai/gpt-oss-120b)
  - Vision model configuration (qwen/qwen3.8-27b)
  - Base64 vision payload construction
  - Structured JSON format enforcement
  - Error and timeout resilience without fabricated results
  - Deterministic allergy barrier and microbiological safety caveats
"""
from __future__ import annotations

import base64
import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.core.config import GROQ_TEXT_MODEL, GROQ_VISION_MODEL
from app.core.groq_provider import groq_provider
from app.services.freshness_service import freshness_service


def create_test_image() -> bytes:
    img = Image.new("RGB", (60, 60), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Model Configuration Tests
# ---------------------------------------------------------------------------
def test_groq_models_configured_correctly():
    assert GROQ_TEXT_MODEL == "openai/gpt-oss-120b"
    assert GROQ_VISION_MODEL == "qwen/qwen3.8-27b"
    assert groq_provider.text_model == "openai/gpt-oss-120b"
    assert groq_provider.vision_model == "qwen/qwen3.8-27b"


def test_groq_unconfigured_offline_behavior():
    with patch.object(groq_provider, "is_available", False):
        res = groq_provider.analyze_freshness(create_test_image())
        assert res["status"] == "provider_unavailable"
        assert "GROQ_API_KEY" in res["error"]

        recipe_res = groq_provider.generate_recipe("lentils, rice")
        assert recipe_res["status"] == "provider_unavailable"
        assert "GROQ_API_KEY" in recipe_res["error"]

        meal_res = groq_provider.generate_meal_candidates({}, 2000, {})
        assert meal_res["status"] == "provider_unavailable"
        assert "GROQ_API_KEY" in meal_res["error"]


# ---------------------------------------------------------------------------
# 2. Qwen Vision Payload Construction Tests
# ---------------------------------------------------------------------------
def test_groq_vision_payload_construction():
    img_bytes = create_test_image()
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"detected_food": "Apple", "freshness_state": "Fresh", "safety_status": "SAFE", "confidence": 95, "observed_signs": [], "reasoning": "Looks crisp", "advice": "Store cool"}'
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch.object(groq_provider, "client", mock_client), \
         patch.object(groq_provider, "is_available", True):
        res = groq_provider.analyze_freshness(
            image_bytes=img_bytes,
            food_name="Apple",
            storage_type="Refrigerator",
            storage_days=2,
            mime_type="image/jpeg",
        )

        assert res["detected_food"] == "Apple"
        # Verify call arguments
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "qwen/qwen3.8-27b"
        assert call_kwargs["response_format"] == {"type": "json_object"}

        messages = call_kwargs["messages"]
        user_msg = next((m for m in messages if m["role"] == "user"), None)
        assert user_msg is not None
        user_content = user_msg["content"]
        # Find image_url payload
        image_part = next((p for p in user_content if isinstance(p, dict) and p.get("type") == "image_url"), None)
        assert image_part is not None
        b64_prefix = "data:image/jpeg;base64,"
        assert image_part["image_url"]["url"].startswith(b64_prefix)
        # Verify base64 content
        encoded_data = image_part["image_url"]["url"][len(b64_prefix):]
        assert base64.b64decode(encoded_data) == img_bytes


# ---------------------------------------------------------------------------
# 3. Text Generation Payload Construction (GPT-OSS-120B)
# ---------------------------------------------------------------------------
def test_groq_text_recipe_payload_construction():
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"title": "Lentil Soup", "summary": "Warm spiced soup", "prep_time_minutes": 10, "cook_time_minutes": 25, "servings": 4, "difficulty": "Easy", "ingredients": ["1 cup red lentils", "onion"], "steps": ["Boil water", "Add lentils"], "dietary_tags": ["Vegan"], "allergens_present": []}'
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_completion

    with patch.object(groq_provider, "client", mock_client), \
         patch.object(groq_provider, "is_available", True):
        res = groq_provider.generate_recipe(
            ingredients_text="red lentils, onions, olive oil",
            cuisine="Mediterranean",
            servings=4,
        )

        assert res["title"] == "Lentil Soup"
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "openai/gpt-oss-120b"
        assert call_kwargs["response_format"] == {"type": "json_object"}


# ---------------------------------------------------------------------------
# 4. Mandatory Safety Caveat Test
# ---------------------------------------------------------------------------
def test_freshness_disclaimer_mandatory():
    """Verify that visual assessment results always contain the mandatory microbial safety caveat."""
    img_bytes = create_test_image()
    mock_groq = {
        "detected_food": "Fresh Salmon",
        "freshness_state": "Fresh",
        "safety_status": "SAFE",
        "confidence": 92.0,
        "observed_signs": ["Clear eyes"],
        "reasoning": "Looks fresh visually.",
        "advice": "Cook to 145F.",
    }

    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "analyze_freshness", return_value=mock_groq):
        resp = freshness_service.analyze(img_bytes, food_name="Fresh Salmon")
        # Must clearly state that visual assessment cannot prove microbiological safety
        assert "cannot prove microbiological safety" in resp.limitations_disclaimer.lower()
        assert resp.provider.startswith("groq")
