"""
FoodVerse AI — Groq Cloud Multimodal & LLM Provider Adapter.

Uses the official groq SDK.
Centralizes provider configuration, structured JSON responses, timeouts, and error handling.
Models:
  - Text: openai/gpt-oss-120b
  - Vision: qwen/qwen3.8-27b
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import (
    GROQ_API_KEY,
    GROQ_MAX_RETRIES,
    GROQ_TEXT_MODEL,
    GROQ_TIMEOUT_SECONDS,
    GROQ_VISION_MODEL,
)

logger = logging.getLogger(__name__)


class GroqProvider:
    """Singleton adapter for Groq Cloud text and vision models."""

    def __init__(self) -> None:
        self.api_key = GROQ_API_KEY
        self.text_model = GROQ_TEXT_MODEL
        self.vision_model = GROQ_VISION_MODEL
        self.timeout = GROQ_TIMEOUT_SECONDS
        self.max_retries = GROQ_MAX_RETRIES
        self.client = None
        self._override_available: Optional[bool] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Groq client if API key is present."""
        if self.api_key and self.api_key.strip():
            try:
                from groq import Groq
                self.client = Groq(
                    api_key=self.api_key.strip(),
                    timeout=self.timeout,
                    max_retries=self.max_retries,
                )
                logger.info(
                    "GroqProvider initialized with text_model: %s, vision_model: %s",
                    self.text_model,
                    self.vision_model,
                )
            except Exception as exc:
                logger.error("Failed to initialize Groq Client: %s", exc)
                self.client = None
        else:
            self.client = None
            logger.info("GroqProvider: GROQ_API_KEY is not set. Service running in offline/provider-unavailable mode.")

    @property
    def is_available(self) -> bool:
        """Return True only if an active Groq client is configured."""
        if self._override_available is not None:
            return self._override_available
        return self.client is not None and bool(self.api_key and self.api_key.strip())

    @is_available.setter
    def is_available(self, val: bool) -> None:
        self._override_available = val

    @is_available.deleter
    def is_available(self) -> None:
        self._override_available = None

    def analyze_freshness(
        self,
        image_bytes: bytes,
        food_name: Optional[str] = None,
        storage_type: Optional[str] = None,
        storage_days: Optional[int] = None,
        mime_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        """
        Analyze food image for visual signs of freshness or spoilage using Groq Vision.
        Model: GROQ_VISION_MODEL (qwen/qwen3.8-27b).
        """
        if not self.is_available:
            return {
                "status": "provider_unavailable",
                "error": "Groq API key is not configured. Please set GROQ_API_KEY in your environment to enable vision freshness inspection.",
            }

        context_str = f"Context: Stored for ~{storage_days or 1} days at {storage_type or 'Room Temp'}."
        if food_name:
            context_str += f" Reported item name: {food_name}."

        system_msg = "You are a professional food quality, biochemical spoilage, and freshness inspection AI. Output ONLY a valid JSON object."
        prompt = f"""Analyze the provided food image carefully for visual signs of freshness, spoilage, or quality degradation.
{context_str}

Evaluate visible color uniformity, surface discoloration, mold bloom, shriveling, slime, or textural degradation.
Allowed freshness_state values: "Fresh", "Marginal", "Spoiled", "Unverified"
Allowed safety_status values: "SAFE", "CAUTION", "UNSAFE", "UNDETERMINED"

Respond strictly in valid JSON matching this exact schema:
{{
  "detected_food": "Identified Food Item",
  "freshness_state": "Fresh",
  "safety_status": "SAFE",
  "confidence": 95.0,
  "observed_signs": ["Natural coloration", "Firm texture"],
  "reasoning": "Detailed 2-3 sentence visual and biochemical explanation.",
  "advice": "Actionable advice on storage or consumption."
}}
CRITICAL: Do NOT guarantee microbiological safety. Visual inspection cannot rule out bacterial toxins or microbial contamination."""

        try:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            messages = [
                {"role": "system", "content": system_msg},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}",
                            },
                        },
                    ],
                },
            ]

            completion = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=2048,
            )
            raw_text = completion.choices[0].message.content or "{}"
            return self._parse_json_response(raw_text)
        except Exception as exc:
            logger.error("Groq analyze_freshness failed: %s", exc)
            return {
                "status": "error",
                "error": f"Freshness analysis request failed: {str(exc)}",
            }

    def generate_recipe(
        self,
        ingredients_text: str,
        image_bytes: Optional[bytes] = None,
        dietary_restrictions: Optional[List[str]] = None,
        cuisine: Optional[str] = None,
        servings: int = 2,
        mime_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        """
        Generate structured gourmet recipe from available ingredients using Groq Text.
        Model: GROQ_TEXT_MODEL (openai/gpt-oss-120b).
        """
        if not self.is_available:
            return {
                "status": "provider_unavailable",
                "error": "Groq API key is not configured. Please set GROQ_API_KEY in your environment to enable AI recipe generation.",
            }

        diet_str = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
        system_msg = "You are a master chef AI in the FoodVerse Smart Kitchen. Output ONLY a valid JSON object."
        prompt = f"""Generate a structured, authentic recipe using the available ingredients.
Ingredients available: {ingredients_text}
Target Servings: {servings}
Cuisine Preference: {cuisine or 'Chef Choice'}
Dietary Restrictions: {diet_str}

Allowed difficulty values: "Easy", "Intermediate", "Advanced"

Respond strictly in valid JSON matching this schema:
{{
  "title": "Dish Name",
  "summary": "1-2 sentence dish description",
  "prep_time_minutes": 15,
  "cook_time_minutes": 25,
  "servings": {servings},
  "difficulty": "Easy",
  "ingredients": ["exact ingredient with quantity and unit"],
  "steps": ["numbered step-by-step cooking instruction"],
  "dietary_tags": ["High Protein", "Vegetarian"],
  "allergens_present": ["None"],
  "estimated_calories_per_serving": 450,
  "estimated_protein_g": 30.0,
  "estimated_carbs_g": 40.0,
  "estimated_fat_g": 12.0
}}"""

        try:
            if image_bytes:
                # If image is attached, invoke vision model
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                messages = [
                    {"role": "system", "content": system_msg},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64_image}",
                                },
                            },
                        ],
                    },
                ]
                model_to_use = self.vision_model
            else:
                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ]
                model_to_use = self.text_model

            completion = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4096,
            )
            raw_text = completion.choices[0].message.content or "{}"
            return self._parse_json_response(raw_text)
        except Exception as exc:
            logger.error("Groq generate_recipe failed: %s", exc)
            return {
                "status": "error",
                "error": f"Recipe generation request failed: {str(exc)}",
            }

    def generate_meal_candidates(
        self,
        profile: Dict[str, Any],
        target_calories: float,
        target_macros: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Generate candidate meal plan matching metabolic calorie and macro targets using Groq Text.
        Model: GROQ_TEXT_MODEL (openai/gpt-oss-120b).
        """
        if not self.is_available:
            return {
                "status": "provider_unavailable",
                "error": "Groq API key is not configured. Please set GROQ_API_KEY in your environment to enable AI meal planning.",
            }

        system_msg = "You are a clinical nutrition and meal planning AI. Output ONLY a valid JSON object."
        prompt = f"""Create a balanced 1-day meal plan (Breakfast, Lunch, Dinner, Snack) tailored to this physiological profile:
Age: {profile.get('age')}
Gender: {profile.get('gender')}
Diet Type: {profile.get('diet_type')}
Cuisine: {profile.get('cuisine_preference', 'Global')}
Strict Excluded Allergens: {profile.get('allergies', 'None')}
Target Daily Calories: {target_calories} kcal
Target Protein: {target_macros.get('protein_g')}g
Target Carbs: {target_macros.get('carbs_g')}g
Target Fat: {target_macros.get('fat_g')}g

CRITICAL SAFETY: DO NOT include ANY of the declared excluded allergens.
Allowed meal_type values: "BREAKFAST", "LUNCH", "DINNER", "SNACK"

Respond strictly in valid JSON matching this schema:
{{
  "meals": [
    {{
      "meal_type": "BREAKFAST",
      "dish_name": "Dish Name",
      "description": "Brief description",
      "ingredients": ["list of specific ingredients"],
      "calories_kcal": 400.0,
      "protein_g": 25.0,
      "carbohydrates_g": 45.0,
      "fat_g": 12.0,
      "allergens": []
    }}
  ],
  "weekly_summary": [
    {{"day": "Mon", "menu": "summary of day"}},
    {{"day": "Tue", "menu": "summary of day"}},
    {{"day": "Wed", "menu": "summary of day"}},
    {{"day": "Thu", "menu": "summary of day"}},
    {{"day": "Fri", "menu": "summary of day"}},
    {{"day": "Sat", "menu": "summary of day"}},
    {{"day": "Sun", "menu": "summary of day"}}
  ],
  "coach_notes": "personalized dietary advice based on target goals"
}}"""

        try:
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ]
            completion = self.client.chat.completions.create(
                model=self.text_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4096,
            )
            raw_text = completion.choices[0].message.content or "{}"
            return self._parse_json_response(raw_text)
        except Exception as exc:
            logger.error("Groq generate_meal_candidates failed: %s", exc)
            return {
                "status": "error",
                "error": f"Meal planning generation request failed: {str(exc)}",
            }

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse clean JSON from model output."""
        try:
            return json.loads(text.strip())
        except Exception:
            # Fallback regex search for JSON block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Model returned non-JSON output: {text[:200]}")


# Global singleton instance
groq_provider = GroqProvider()
