"""
FoodVerse AI — Nutrition estimation service.

Responsibilities:
- Map a recognized food label to nutrition reference data.
- Return per-100g values or scale to user-confirmed serving.
- Validate all numeric fields; never substitute zeros for missing data.
- Keep health-score calculation isolated and unavailable until approved.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.repositories.nutrition_repository import NutritionRecord, nutrition_repository
from app.schemas.food_analysis import HealthScore, NutritionEstimate

logger = logging.getLogger(__name__)


def estimate_nutrition(
    canonical_food_id: Optional[str],
    serving_grams: Optional[float] = None,
) -> tuple[NutritionEstimate, list[str], list[str]]:
    """
    Look up nutrition data for a canonical food ID and optionally scale
    to a user-confirmed serving size.

    Returns:
        (NutritionEstimate, assumptions, warnings)

    Null nutrients mean unavailable, not zero. This function never
    fabricates values.
    """
    assumptions: list[str] = []
    warnings: list[str] = []

    # No canonical ID → nutrition unavailable
    if not canonical_food_id:
        warnings.append("No food label available for nutrition lookup.")
        return _unavailable_estimate(), assumptions, warnings

    # Look up in nutrition repository
    record = nutrition_repository.lookup(canonical_food_id)

    if record is None:
        if nutrition_repository.is_ready:
            warnings.append(
                f"No nutrition data found for '{canonical_food_id.replace('_', ' ')}'. "
                "Nutrient values are unavailable."
            )
        else:
            warnings.append(
                "Nutrition reference data is not loaded. "
                "Nutrient values are unavailable."
            )
        return _unavailable_estimate(), assumptions, warnings

    # Determine serving basis
    if serving_grams is not None and serving_grams > 0:
        return _scale_to_portion(record, serving_grams, assumptions, warnings)
    else:
        return _per_100g(record, assumptions, warnings)


def _per_100g(
    record: NutritionRecord,
    assumptions: list[str],
    warnings: list[str],
) -> tuple[NutritionEstimate, list[str], list[str]]:
    """Return reference values per 100 g."""
    assumptions.append("Nutrition values are per 100 g serving (reference values).")
    assumptions.append(f"Source: {record.source}")

    estimate = NutritionEstimate(
        basis="per_100_g",
        serving_grams=100.0,
        calories_kcal=round(record.calories_kcal, 1),
        protein_g=round(record.protein_g, 1),
        carbohydrates_g=round(record.carbohydrates_g, 1),
        fat_g=round(record.fat_g, 1),
        source=record.source,
    )
    return estimate, assumptions, warnings


def _scale_to_portion(
    record: NutritionRecord,
    serving_grams: float,
    assumptions: list[str],
    warnings: list[str],
) -> tuple[NutritionEstimate, list[str], list[str]]:
    """Scale per-100g reference to user-confirmed serving size."""
    # Guard against unreasonable portion sizes
    if serving_grams > 5000:
        warnings.append(
            f"Serving size of {serving_grams}g is unusually large. "
            "Please verify the amount."
        )
    if serving_grams < 1:
        warnings.append(
            f"Serving size of {serving_grams}g is very small. "
            "Please verify the amount."
        )

    scale = serving_grams / 100.0
    assumptions.append(
        f"Nutrition values scaled to user-confirmed serving of {serving_grams}g."
    )
    assumptions.append(f"Source: {record.source}")

    estimate = NutritionEstimate(
        basis="user_portion",
        serving_grams=round(serving_grams, 1),
        calories_kcal=round(record.calories_kcal * scale, 1),
        protein_g=round(record.protein_g * scale, 1),
        carbohydrates_g=round(record.carbohydrates_g * scale, 1),
        fat_g=round(record.fat_g * scale, 1),
        source=record.source,
    )
    return estimate, assumptions, warnings


def _unavailable_estimate() -> NutritionEstimate:
    """Return a nutrition estimate with all values explicitly unavailable."""
    return NutritionEstimate(
        basis="unavailable",
        serving_grams=None,
        calories_kcal=None,
        protein_g=None,
        carbohydrates_g=None,
        fat_g=None,
        source=None,
    )


def compute_health_score() -> HealthScore:
    """
    Compute health score.

    Formula, scale, and validation are NOT approved for v1.
    Always returns null/unavailable.
    """
    return HealthScore(
        value=None,
        scale=None,
        rationale=["Health score formula is pending approval. Score is unavailable."],
        method_version=None,
    )
