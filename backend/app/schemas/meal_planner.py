"""
FoodVerse AI — Personalized Meal Planner Schemas.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class MealPlanProfile(BaseModel):
    """User physiological parameters and dietary requirements."""
    age: int = Field(..., ge=12, le=120)
    gender: Literal["Female", "Male", "Other"] = "Female"
    height_cm: float = Field(..., ge=100.0, le=250.0)
    weight_kg: float = Field(..., ge=30.0, le=300.0)
    activity_level: Literal["Sedentary", "Light", "Moderate", "Active", "Very Active"] = "Moderate"
    goal: Literal["Weight Loss", "Maintenance", "Muscle Gain"] = "Maintenance"
    diet_type: Literal["Standard", "High Protein", "Keto", "Mediterranean", "Vegetarian", "Vegan"] = "Standard"
    cuisine_preference: Optional[str] = "Global"
    allergies: str = Field(default="", description="Comma-separated declared allergens")
    medical_conditions: Optional[str] = ""


class MealItem(BaseModel):
    """Individual meal within the daily plan."""
    meal_type: Literal["BREAKFAST", "LUNCH", "DINNER", "SNACK"]
    dish_name: str
    description: str
    ingredients: List[str]
    calories_kcal: float
    protein_g: float
    carbohydrates_g: float
    fat_g: float
    allergens: List[str] = Field(default_factory=list)


class DailyMealPlan(BaseModel):
    """Today's meal plan with totals."""
    day: str = "Today"
    calories_total: float
    protein_total_g: float
    carbs_total_g: float
    fat_total_g: float
    meals: List[MealItem]


class CalculatedTargets(BaseModel):
    """Metabolic engine calculated targets."""
    bmr_kcal: float
    tdee_kcal: float
    target_calories: float
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    hydration_liters: float


class MealPlanResponse(BaseModel):
    """Complete personalized meal plan response."""
    request_id: str
    status: Literal["success", "allergy_conflict", "constraint_error", "provider_unavailable", "generation_failed"]
    calculated_targets: CalculatedTargets
    adherence_score_pct: int = 90
    today_plan: DailyMealPlan
    weekly_overview: List[Dict[str, str]] = Field(default_factory=list)
    allergy_safety_cleared: bool = True
    excluded_allergens: List[str] = Field(default_factory=list)
    coach_notes: str
    warnings: List[str] = Field(default_factory=list)
    orchestration: str = "LangGraph Agentic StateGraph (Groq openai/gpt-oss-120b + Hard Allergy Barrier)"
    report_id: Optional[str] = Field(default=None, description="Persisted analysis report ID")
