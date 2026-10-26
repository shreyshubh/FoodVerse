"""
FoodVerse AI — Nutrition data repository adapter.

Loads a local JSON reference file mapping canonical food IDs to
per-100g macronutrient data sourced from USDA FoodData Central.

Designed to be replaceable: swap to a database or API without changing
the service interface.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import NUTRITION_REFERENCE_PATH

logger = logging.getLogger(__name__)


class NutritionRecord:
    """A single nutrition reference record (per 100 g)."""

    __slots__ = (
        "food_id",
        "display_name",
        "calories_kcal",
        "protein_g",
        "carbohydrates_g",
        "fat_g",
        "source",
    )

    def __init__(
        self,
        food_id: str,
        display_name: str,
        calories_kcal: float,
        protein_g: float,
        carbohydrates_g: float,
        fat_g: float,
        source: str = "USDA FoodData Central",
    ):
        self.food_id = food_id
        self.display_name = display_name
        self.calories_kcal = calories_kcal
        self.protein_g = protein_g
        self.carbohydrates_g = carbohydrates_g
        self.fat_g = fat_g
        self.source = source


class NutritionRepository:
    """
    Adapter for nutrition reference data.

    Loads a JSON file at startup. Returns None for unknown food IDs
    instead of fabricating values.
    """

    def __init__(self) -> None:
        self._data: dict[str, NutritionRecord] = {}
        self._ready = False
        self._init_error: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        """Load the nutrition reference JSON file."""
        try:
            ref_path = Path(NUTRITION_REFERENCE_PATH)
            if not ref_path.exists():
                raise FileNotFoundError(
                    f"Nutrition reference file not found at {ref_path}."
                )

            with open(ref_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if not isinstance(raw, dict):
                raise ValueError("Nutrition reference must be a JSON object.")

            for food_id, entry in raw.items():
                self._data[food_id] = NutritionRecord(
                    food_id=food_id,
                    display_name=entry.get("display_name", food_id.replace("_", " ").title()),
                    calories_kcal=float(entry["calories_kcal"]),
                    protein_g=float(entry["protein_g"]),
                    carbohydrates_g=float(entry["carbohydrates_g"]),
                    fat_g=float(entry["fat_g"]),
                    source=entry.get("source", "USDA FoodData Central"),
                )

            self._ready = True
            logger.info("Nutrition reference loaded: %d entries.", len(self._data))

        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            logger.warning("Nutrition reference initialization failed: %s", exc)

    def lookup(self, canonical_food_id: str) -> Optional[NutritionRecord]:
        """
        Look up nutrition data by canonical food ID.

        Returns None if the food ID is not found — callers must not
        substitute zero values for missing data.
        """
        if not self._ready and self._init_error is None:
            self.initialize()
        if not self._ready:
            return None
        return self._data.get(canonical_food_id)

    @property
    def available_food_ids(self) -> list[str]:
        """List all food IDs in the reference."""
        return list(self._data.keys())


# Module-level singleton — initialized by app startup
nutrition_repository = NutritionRepository()
