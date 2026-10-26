"""
FoodVerse AI — Smart Kitchen & Recipe Schemas.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class RecipeNutritionEstimate(BaseModel):
    """Estimated nutrition breakdown per serving."""
    calories_kcal: Optional[float] = None
    protein_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    fat_g: Optional[float] = None
    source: str = "USDA Reference Estimation"


class RecipeResponse(BaseModel):
    """Structured response for AI recipe generation."""
    request_id: str
    status: Literal["success", "clarification_needed", "provider_unavailable", "dietary_violation"]
    title: str
    summary: str
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    difficulty: Literal["Easy", "Intermediate", "Advanced"]
    ingredients: List[str]
    steps: List[str]
    nutrition: RecipeNutritionEstimate
    dietary_tags: List[str] = Field(default_factory=list)
    allergens_present: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    orchestration: str = Field(default="LangGraph Agentic StateGraph (Groq openai/gpt-oss-120b)", description="Pipeline architecture")
    report_id: Optional[str] = Field(default=None, description="Persisted analysis report ID")
