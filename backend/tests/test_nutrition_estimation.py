"""
FoodVerse AI — Tests for the nutrition estimation service.

Covers: per-100g lookup, portion scaling, missing entries,
boundary conditions, and health score unavailability.
"""

from __future__ import annotations

import pytest

from app.services.nutrition_estimation import (
    _unavailable_estimate,
    compute_health_score,
    estimate_nutrition,
)


class TestEstimateNutrition:
    """Tests for the nutrition estimation function."""

    def test_known_food_returns_per_100g(self):
        """Known food with no serving_grams returns per_100_g basis."""
        nutrition, assumptions, warnings = estimate_nutrition("pizza")
        assert nutrition.basis == "per_100_g"
        assert nutrition.serving_grams == 100.0
        assert nutrition.calories_kcal is not None
        assert nutrition.calories_kcal > 0
        assert nutrition.protein_g is not None
        assert nutrition.carbohydrates_g is not None
        assert nutrition.fat_g is not None
        assert nutrition.source is not None
        assert len(warnings) == 0

    def test_known_food_with_serving_scales(self):
        """Known food with serving_grams returns user_portion basis with scaled values."""
        nutrition_100g, _, _ = estimate_nutrition("pizza")
        nutrition_200g, _, _ = estimate_nutrition("pizza", serving_grams=200.0)

        assert nutrition_200g.basis == "user_portion"
        assert nutrition_200g.serving_grams == 200.0
        # Values should be approximately 2x the per-100g values
        assert abs(nutrition_200g.calories_kcal - nutrition_100g.calories_kcal * 2) < 0.2

    def test_unknown_food_returns_unavailable(self):
        """Unknown food ID returns unavailable nutrition with warning."""
        nutrition, assumptions, warnings = estimate_nutrition("nonexistent_food_xyz")
        assert nutrition.basis == "unavailable"
        assert nutrition.calories_kcal is None
        assert nutrition.protein_g is None
        assert nutrition.carbohydrates_g is None
        assert nutrition.fat_g is None
        assert len(warnings) > 0

    def test_none_food_id_returns_unavailable(self):
        """None food ID returns unavailable nutrition."""
        nutrition, assumptions, warnings = estimate_nutrition(None)
        assert nutrition.basis == "unavailable"
        assert nutrition.calories_kcal is None

    def test_empty_food_id_returns_unavailable(self):
        """Empty string food ID returns unavailable nutrition."""
        nutrition, assumptions, warnings = estimate_nutrition("")
        assert nutrition.basis == "unavailable"

    def test_very_large_serving_warns(self):
        """Very large serving size should produce a warning."""
        nutrition, assumptions, warnings = estimate_nutrition("pizza", serving_grams=6000.0)
        assert any("unusually large" in w for w in warnings)

    def test_very_small_serving_warns(self):
        """Very small serving size should produce a warning."""
        nutrition, assumptions, warnings = estimate_nutrition("pizza", serving_grams=0.5)
        assert any("very small" in w for w in warnings)

    def test_null_values_mean_unavailable_not_zero(self):
        """Null nutrient values must mean unavailable, never zero."""
        nutrition, _, _ = estimate_nutrition("nonexistent_food_xyz")
        # All should be None, not 0
        assert nutrition.calories_kcal is None
        assert nutrition.protein_g is None
        assert nutrition.carbohydrates_g is None
        assert nutrition.fat_g is None

    def test_assumptions_include_source(self):
        """Assumptions should mention the data source."""
        _, assumptions, _ = estimate_nutrition("pizza")
        sources = [a for a in assumptions if "Source" in a or "USDA" in a]
        assert len(sources) > 0

    def test_scaling_arithmetic_precision(self):
        """Verify that scaling arithmetic rounds correctly."""
        nutrition, _, _ = estimate_nutrition("pizza", serving_grams=150.0)
        assert nutrition.serving_grams == 150.0
        # All values should be rounded to 1 decimal place
        if nutrition.calories_kcal is not None:
            assert nutrition.calories_kcal == round(nutrition.calories_kcal, 1)


class TestUnavailableEstimate:
    """Tests for the unavailable estimate helper."""

    def test_all_fields_none(self):
        """Unavailable estimate should have all nutrient fields as None."""
        estimate = _unavailable_estimate()
        assert estimate.basis == "unavailable"
        assert estimate.serving_grams is None
        assert estimate.calories_kcal is None
        assert estimate.protein_g is None
        assert estimate.carbohydrates_g is None
        assert estimate.fat_g is None
        assert estimate.source is None


class TestHealthScore:
    """Tests for the health score stub."""

    def test_health_score_unavailable(self):
        """Health score must be null/unavailable until formula is approved."""
        score = compute_health_score()
        assert score.value is None
        assert score.scale is None
        assert score.method_version is None
        assert len(score.rationale) > 0
        assert any("pending" in r.lower() or "unavailable" in r.lower() for r in score.rationale)
