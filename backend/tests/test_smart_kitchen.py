"""
FoodVerse AI — Smart Kitchen Recipe Agent Tests.
"""
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient

from app.main import app
from app.agents.recipe_graph import execute_recipe_generation
from app.core.groq_provider import groq_provider


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_recipe_input_validation(client):
    """Empty ingredient description is rejected."""
    resp = client.post(
        "/api/v1/recipes/generate",
        data={"ingredients_text": "   "},
    )
    assert resp.status_code == 400


def test_recipe_provider_unavailable_when_no_key():
    """Returns explicit provider_unavailable envelope when key is missing (no fake biryani)."""
    with patch.object(groq_provider, "is_available", False):
        resp = execute_recipe_generation(
            ingredients_text="eggs, spinach, cheddar cheese",
            servings=2,
        )
        assert resp.status == "provider_unavailable"
        assert resp.title == "Service Unavailable"
        assert "Groq API key is not configured" in resp.summary


def test_recipe_langgraph_dietary_violation_filter():
    """If candidate recipe violates declared dietary restrictions, agent flags the violation."""
    mock_chicken_recipe = {
        "title": "Creamy Chicken Alfredo",
        "summary": "Classic chicken alfredo with pasta.",
        "prep_time_minutes": 15,
        "cook_time_minutes": 20,
        "servings": 2,
        "difficulty": "Intermediate",
        "ingredients": ["8 oz fettuccine", "1 lb chicken breast", "1 cup heavy cream", "parmesan"],
        "steps": ["Boil pasta.", "Cook chicken.", "Make sauce."],
        "dietary_tags": ["High Protein"],
        "allergens_present": ["dairy", "gluten"],
    }

    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "generate_recipe", return_value=mock_chicken_recipe):
        # User specified Vegetarian dietary restriction
        resp = execute_recipe_generation(
            ingredients_text="pasta, cream, chicken",
            dietary_restrictions=["vegetarian"],
            servings=2,
        )
        assert resp.status == "dietary_violation"
        assert "chicken" in resp.summary.lower()
