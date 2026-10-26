"""
FoodVerse AI — Personalized Meal Planner Route.

Executes LangGraph meal planner workflow with Mifflin-St Jeor engine,
Groq openai/gpt-oss-120b dish synthesis, and deterministic allergy safety barrier.
Persists validated meal plan reports in MongoDB analysis_reports.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.meal_planner_graph import execute_meal_plan_generation
from app.core.session import get_current_owner_id
from app.db.report_repository import report_repository
from app.schemas.meal_planner import MealPlanProfile, MealPlanResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/meal-plans/generate",
    response_model=MealPlanResponse,
    summary="Generate personalized nutrition plan with deterministic BMR and allergy barrier",
)
async def generate_meal_plan(
    profile: MealPlanProfile,
    owner_id: str = Depends(get_current_owner_id),
) -> MealPlanResponse:
    """Execute LangGraph meal planning graph with Mifflin-St Jeor engine and strict allergy filter."""
    try:
        response = execute_meal_plan_generation(profile)

        # Persistence policy:
        # A failed allergy validation outcome must NEVER be marked as completed or successfully validated!
        is_successful_plan = (response.status == "success") and (response.allergy_safety_cleared is True)
        report_status = "completed" if is_successful_plan else "failed"

        # Sanitize profile to store only necessary constraints
        safe_constraints = {
            "diet_type": profile.diet_type,
            "goal": profile.goal,
            "activity_level": profile.activity_level,
            "cuisine_preference": profile.cuisine_preference,
            "excluded_allergens": response.excluded_allergens,
        }

        report_doc = await report_repository.create_report(
            owner_id=owner_id,
            feature="meal_plan",
            status=report_status,
            input_data=safe_constraints,
            result_data=response.model_dump(),
            model_info={
                "provider": "groq",
                "model_id": "openai/gpt-oss-120b",
            },
            metrics={
                "target_calories": response.calculated_targets.target_calories,
                "adherence_score_pct": response.adherence_score_pct,
                "allergy_safety_cleared": response.allergy_safety_cleared,
            },
            error_metadata={"violations": response.warnings} if not is_successful_plan else None,
        )
        if report_doc:
            response.report_id = report_doc.get("id")

        return response
    except Exception as exc:
        logger.error("Meal planning execution failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "INTERNAL_ERROR", "message": f"Meal plan generation failed: {str(exc)}"}},
        )
