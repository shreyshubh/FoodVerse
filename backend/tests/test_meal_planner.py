"""
FoodVerse AI — Personalized Meal Planner & Deterministic Allergy Safety Barrier Tests.
"""
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient

from app.main import app
from app.agents.meal_planner_graph import execute_meal_plan_generation
from app.core.groq_provider import groq_provider
from app.schemas.meal_planner import MealPlanProfile
from app.services.allergy_validator import allergy_validator


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_mifflin_st_jeor_deterministic_calculation():
    """Verify BMR, TDEE, and macro math without trusting any model."""
    # Profile: Female, 25yo, 60kg, 165cm, Moderate activity (1.55), Maintenance
    # BMR = (10 * 60) + (6.25 * 165) - (5 * 25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
    # TDEE = 1345.25 * 1.55 = 2085.1
    profile = MealPlanProfile(
        age=25,
        gender="Female",
        height_cm=165.0,
        weight_kg=60.0,
        activity_level="Moderate",
        goal="Maintenance",
        diet_type="Standard",
        allergies="",
    )
    with patch.object(groq_provider, "is_available", False):
        resp = execute_meal_plan_generation(profile)
        targets = resp.calculated_targets
        assert targets.bmr_kcal == 1345.2
        assert targets.tdee_kcal == 2085.1
        assert targets.target_calories == 2085.0
        # When unconfigured, it must report provider_unavailable, not success!
        assert resp.status == "provider_unavailable"
        assert resp.allergy_safety_cleared is False
        assert len(resp.today_plan.meals) == 0


def test_meal_planner_unconfigured_provider_fails_explicitly(client):
    """When GROQ_API_KEY is not set, endpoint must report provider_unavailable with empty meals."""
    with patch.object(groq_provider, "is_available", False):
        resp = client.post(
            "/api/v1/meal-plans/generate",
            json={
                "age": 28,
                "gender": "Male",
                "height_cm": 180.0,
                "weight_kg": 78.0,
                "activity_level": "Moderate",
                "goal": "Weight Loss",
                "diet_type": "Standard",
                "allergies": "peanuts",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "provider_unavailable"
        assert data["allergy_safety_cleared"] is False
        assert len(data["today_plan"]["meals"]) == 0
        assert data["today_plan"]["calories_total"] == 0.0


def test_meal_planner_empty_candidates_fails_explicitly():
    """If provider returns an empty candidate list, status must be generation_failed, not success."""
    profile = MealPlanProfile(
        age=30,
        gender="Female",
        height_cm=165.0,
        weight_kg=65.0,
        activity_level="Light",
        goal="Maintenance",
        diet_type="Standard",
        allergies="",
    )
    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "generate_meal_candidates", return_value={"status": "success", "meals": []}):
        resp = execute_meal_plan_generation(profile)
        assert resp.status == "generation_failed"
        assert resp.allergy_safety_cleared is False
        assert len(resp.today_plan.meals) == 0


def test_meal_planner_successful_generation_clears_safety():
    """Only non-empty, validated candidate meals can produce status=success and allergy_safety_cleared=True."""
    safe_meals = {
        "meals": [
            {
                "meal_type": "BREAKFAST",
                "dish_name": "Avocado Toast",
                "description": "Whole grain toast with avocado.",
                "ingredients": ["whole grain bread", "avocado", "olive oil"],
                "calories_kcal": 380.0,
                "protein_g": 9.0,
                "carbohydrates_g": 35.0,
                "fat_g": 22.0,
                "allergens": [],
            },
            {
                "meal_type": "LUNCH",
                "dish_name": "Quinoa Salad",
                "description": "Quinoa with mixed vegetables.",
                "ingredients": ["quinoa", "cucumber", "bell pepper", "lemon"],
                "calories_kcal": 450.0,
                "protein_g": 14.0,
                "carbohydrates_g": 65.0,
                "fat_g": 12.0,
                "allergens": [],
            },
        ],
        "weekly_summary": [{"day": "Monday", "menu": "Avocado toast & Quinoa bowl"}],
        "coach_notes": "Balanced micronutrients.",
    }

    profile = MealPlanProfile(
        age=28,
        gender="Female",
        height_cm=168.0,
        weight_kg=62.0,
        activity_level="Moderate",
        goal="Maintenance",
        diet_type="Vegetarian",
        allergies="Peanuts",
    )

    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "generate_meal_candidates", return_value=safe_meals):
        resp = execute_meal_plan_generation(profile)
        assert resp.status == "success"
        assert resp.allergy_safety_cleared is True
        assert len(resp.today_plan.meals) == 2
        assert resp.today_plan.calories_total == 830.0


def test_allergy_safety_barrier_detects_and_blocks_allergen():
    """CRITICAL SAFETY TEST: If generated meal contains peanut butter when user has peanut allergy, barrier blocks it!"""
    unsafe_meals = {
        "meals": [
            {
                "meal_type": "BREAKFAST",
                "dish_name": "Oatmeal with Peanut Butter",
                "description": "Warm oats with a dollop of peanut butter.",
                "ingredients": ["rolled oats", "peanut butter", "almond milk"],
                "calories_kcal": 400.0,
                "protein_g": 15.0,
                "carbohydrates_g": 50.0,
                "fat_g": 16.0,
                "allergens": ["peanut"],
            }
        ],
        "weekly_summary": [],
        "coach_notes": "Eat well.",
    }

    profile = MealPlanProfile(
        age=30,
        gender="Male",
        height_cm=175.0,
        weight_kg=75.0,
        activity_level="Active",
        goal="Maintenance",
        diet_type="High Protein",
        allergies="Peanuts, Shellfish",
    )

    with patch.object(groq_provider, "is_available", True), \
         patch.object(groq_provider, "generate_meal_candidates", return_value=unsafe_meals):
        resp = execute_meal_plan_generation(profile)
        # Must catch the allergy conflict and NOT clear safety!
        assert resp.status == "allergy_conflict"
        assert resp.allergy_safety_cleared is False
        assert "peanut" in resp.coach_notes.lower()
        # Meals must be emptied so the user cannot see or consume unsafe meals
        assert len(resp.today_plan.meals) == 0


def test_allergen_normalization_and_synonyms():
    """Verify allergen synonyms match correctly (e.g. 'egg' matches 'mayonnaise', 'dairy' matches 'ghee')."""
    is_safe, violations, _ = allergy_validator.validate_meal_ingredients(
        meal_name="Turkey Club Sandwich",
        ingredients=["whole grain bread", "turkey breast", "mayonnaise", "tomato"],
        declared_allergens=["egg"],
    )
    assert is_safe is False
    assert any("mayonnaise" in v.lower() for v in violations)


def test_invalid_profile_age_rejected(client):
    """Negative or unrealistic age is rejected."""
    resp = client.post(
        "/api/v1/meal-plans/generate",
        json={
            "age": 5,  # Min age is 12
            "gender": "Female",
            "height_cm": 165.0,
            "weight_kg": 60.0,
        },
    )
    assert resp.status_code == 422
