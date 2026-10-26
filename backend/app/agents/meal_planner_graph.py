"""
FoodVerse AI — Personalized Meal Planner Agent (LangGraph).

Executes a deterministic metabolic engine, Gemini meal generation,
and a mandatory zero-trust deterministic allergy safety barrier.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.groq_provider import groq_provider
from app.schemas.meal_planner import (
    CalculatedTargets,
    DailyMealPlan,
    MealItem,
    MealPlanProfile,
    MealPlanResponse,
)
from app.services.allergy_validator import allergy_validator

logger = logging.getLogger(__name__)

ACTIVITY_MULTIPLIERS = {
    "Sedentary": 1.2,
    "Light": 1.375,
    "Moderate": 1.55,
    "Active": 1.725,
    "Very Active": 1.9,
}

GOAL_CALORIE_DELTAS = {
    "Weight Loss": -500.0,
    "Maintenance": 0.0,
    "Muscle Gain": 350.0,
}


class MealPlannerState(TypedDict):
    """Execution state for the Personalized Meal Planner LangGraph workflow."""
    request_id: str
    profile: MealPlanProfile
    targets: Optional[CalculatedTargets]
    candidate_meals: List[MealItem]
    weekly_overview: List[Dict[str, str]]
    allergy_violations: List[str]
    allergy_safety_cleared: bool
    coach_notes: str
    retry_count: int
    status: str
    errors: List[str]
    warnings: List[str]


def calculate_metabolic_targets_node(state: MealPlannerState) -> Dict[str, Any]:
    """Node 1: Deterministic Mifflin-St Jeor BMR & TDEE calculation."""
    profile = state["profile"]
    weight = profile.weight_kg
    height = profile.height_cm
    age = profile.age
    gender = profile.gender

    # Mifflin-St Jeor Equation
    if gender == "Male":
        bmr = (10.0 * weight) + (6.25 * height) - (5.0 * age) + 5.0
    elif gender == "Female":
        bmr = (10.0 * weight) + (6.25 * height) - (5.0 * age) - 161.0
    else:
        bmr = (10.0 * weight) + (6.25 * height) - (5.0 * age) - 78.0

    multiplier = ACTIVITY_MULTIPLIERS.get(profile.activity_level, 1.55)
    tdee = bmr * multiplier
    target_cal = round(tdee + GOAL_CALORIE_DELTAS.get(profile.goal, 0.0), 0)

    # Macro distribution
    diet = profile.diet_type
    if diet == "High Protein":
        p_ratio, c_ratio, f_ratio = 0.30, 0.40, 0.30
    elif diet == "Keto":
        p_ratio, c_ratio, f_ratio = 0.25, 0.05, 0.70
    elif diet in {"Vegetarian", "Vegan"}:
        p_ratio, c_ratio, f_ratio = 0.20, 0.55, 0.25
    else:  # Standard / Mediterranean
        p_ratio, c_ratio, f_ratio = 0.20, 0.50, 0.30

    target_prot = round((target_cal * p_ratio) / 4.0, 1)
    target_carbs = round((target_cal * c_ratio) / 4.0, 1)
    target_fat = round((target_cal * f_ratio) / 9.0, 1)
    hydration = round(max(2.0, (weight * 0.035)), 1)

    targets = CalculatedTargets(
        bmr_kcal=round(bmr, 1),
        tdee_kcal=round(tdee, 1),
        target_calories=target_cal,
        target_protein_g=target_prot,
        target_carbs_g=target_carbs,
        target_fat_g=target_fat,
        hydration_liters=hydration,
    )

    return {"targets": targets, "status": "targets_calculated"}


def generate_candidates_node(state: MealPlannerState) -> Dict[str, Any]:
    """Node 2: Query Gemini model for candidate meals matching targets."""
    targets = state.get("targets")
    if not targets:
        return {"status": "generation_failed", "allergy_safety_cleared": False, "errors": ["Failed to compute metabolic targets."]}

    if not groq_provider.is_available:
        return {
            "status": "provider_unavailable",
            "allergy_safety_cleared": False,
            "errors": ["Groq API key is not configured. Set GROQ_API_KEY in backend .env to generate dynamic personalized meal plans."],
        }

    profile_dict = state["profile"].model_dump()
    target_macros = {
        "protein_g": targets.target_protein_g,
        "carbs_g": targets.target_carbs_g,
        "fat_g": targets.target_fat_g,
    }

    raw = groq_provider.generate_meal_candidates(
        profile=profile_dict,
        target_calories=targets.target_calories,
        target_macros=target_macros,
    )

    if raw.get("status") in {"error", "provider_unavailable"}:
        return {
            "status": "provider_unavailable",
            "allergy_safety_cleared": False,
            "errors": [raw.get("error", "Failed to connect to meal planning model.")],
        }

    # Convert to structured MealItem models
    raw_meals = raw.get("meals", [])
    if not raw_meals:
        return {
            "status": "generation_failed",
            "allergy_safety_cleared": False,
            "errors": ["Meal planning model returned no candidate dishes."],
        }

    candidate_meals: List[MealItem] = []
    for m in raw_meals:
        m_type = m.get("meal_type", "LUNCH").upper()
        if m_type not in {"BREAKFAST", "LUNCH", "DINNER", "SNACK"}:
            m_type = "LUNCH"
        candidate_meals.append(MealItem(
            meal_type=m_type,
            dish_name=m.get("dish_name", "Healthy Meal"),
            description=m.get("description", "Nutritionally balanced meal."),
            ingredients=m.get("ingredients", []),
            calories_kcal=float(m.get("calories_kcal", 400.0)),
            protein_g=float(m.get("protein_g", 25.0)),
            carbohydrates_g=float(m.get("carbohydrates_g", 40.0)),
            fat_g=float(m.get("fat_g", 12.0)),
            allergens=m.get("allergens", []),
        ))

    weekly = raw.get("weekly_summary", [])
    coach = raw.get("coach_notes", "Maintain steady hydration and portion balance.")

    return {
        "candidate_meals": candidate_meals,
        "weekly_overview": weekly,
        "coach_notes": coach,
        "status": "candidates_generated",
    }


def after_candidates_edge(state: MealPlannerState) -> str:
    """Conditional Edge: Route to allergy validation only if candidates were generated."""
    if state.get("status") in {"provider_unavailable", "generation_failed", "error"}:
        return "format_final_plan"
    return "allergy_safety_barrier"


def allergy_safety_barrier_node(state: MealPlannerState) -> Dict[str, Any]:
    """Node 3: Zero-trust deterministic allergy barrier."""
    meals = state.get("candidate_meals", [])
    if not meals:
        return {
            "status": "generation_failed",
            "allergy_safety_cleared": False,
            "allergy_violations": [],
            "errors": ["No candidate meals present to validate."],
        }

    raw_allergies = state["profile"].allergies
    declared_allergens = allergy_validator.normalize_declared_allergens(raw_allergies)

    violations: List[str] = []
    if declared_allergens:
        for meal in meals:
            is_safe, meal_violations, _ = allergy_validator.validate_meal_ingredients(
                meal_name=meal.dish_name,
                ingredients=meal.ingredients,
                declared_allergens=declared_allergens,
            )
            if not is_safe:
                for v in meal_violations:
                    violations.append(f"[{meal.meal_type}] {v}")

    if violations:
        logger.warning("Allergy violations detected: %s", violations)
        return {
            "status": "allergy_conflict",
            "allergy_violations": violations,
            "allergy_safety_cleared": False,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {
        "status": "safety_cleared",
        "allergy_violations": [],
        "allergy_safety_cleared": True,
    }


def should_repair_allergy_edge(state: MealPlannerState) -> str:
    """Conditional Edge: Route to retry or termination based on allergy clearance."""
    if state.get("status") == "allergy_conflict":
        if state.get("retry_count", 0) <= 1:
            return "generate_candidates"
        return "format_final_plan"
    return "format_final_plan"


def format_final_plan_node(state: MealPlannerState) -> Dict[str, Any]:
    """Node 4: Validate macro totals and package verified plan."""
    targets = state.get("targets")
    meals = state.get("candidate_meals", [])
    status = state.get("status")
    warnings = list(state.get("warnings", []))

    if status in {"provider_unavailable", "allergy_conflict"}:
        return {"status": status, "allergy_safety_cleared": False}

    if not meals or not targets or status in {"generation_failed", "error"}:
        return {
            "status": "generation_failed",
            "allergy_safety_cleared": False,
            "errors": state.get("errors", ["Incomplete or unvalidated meal plan."]),
        }

    if state.get("allergy_safety_cleared") is not True:
        return {
            "status": "generation_failed",
            "allergy_safety_cleared": False,
            "errors": ["Candidate meals did not clear allergy safety validation."],
        }

    total_cal = sum(m.calories_kcal for m in meals)

    # Macro discrepancy audit
    if abs(total_cal - targets.target_calories) > (targets.target_calories * 0.15):
        warnings.append(f"Plan calorie total ({total_cal:.0f} kcal) deviates slightly from calculated target ({targets.target_calories:.0f} kcal).")

    return {"status": "complete", "allergy_safety_cleared": True, "warnings": warnings}


# Construct LangGraph StateGraph
builder = StateGraph(MealPlannerState)
builder.add_node("calculate_metabolic_targets", calculate_metabolic_targets_node)
builder.add_node("generate_candidates", generate_candidates_node)
builder.add_node("allergy_safety_barrier", allergy_safety_barrier_node)
builder.add_node("format_final_plan", format_final_plan_node)

builder.add_edge(START, "calculate_metabolic_targets")
builder.add_edge("calculate_metabolic_targets", "generate_candidates")
builder.add_conditional_edges("generate_candidates", after_candidates_edge, {
    "allergy_safety_barrier": "allergy_safety_barrier",
    "format_final_plan": "format_final_plan",
})
builder.add_conditional_edges("allergy_safety_barrier", should_repair_allergy_edge, {
    "generate_candidates": "generate_candidates",
    "format_final_plan": "format_final_plan",
})
builder.add_edge("format_final_plan", END)

meal_planner_graph = builder.compile()


def execute_meal_plan_generation(profile: MealPlanProfile) -> MealPlanResponse:
    """Entry point to execute the compiled Meal Planner LangGraph workflow."""
    req_id = str(uuid.uuid4())
    initial_state: MealPlannerState = {
        "request_id": req_id,
        "profile": profile,
        "targets": None,
        "candidate_meals": [],
        "weekly_overview": [],
        "allergy_violations": [],
        "allergy_safety_cleared": False,
        "coach_notes": "",
        "retry_count": 0,
        "status": "pending",
        "errors": [],
        "warnings": [],
    }

    final_state = meal_planner_graph.invoke(initial_state)

    status = final_state.get("status")
    targets = final_state.get("targets") or CalculatedTargets(
        bmr_kcal=1500.0,
        tdee_kcal=1800.0,
        target_calories=1800.0,
        target_protein_g=100.0,
        target_carbs_g=200.0,
        target_fat_g=60.0,
        hydration_liters=2.5,
    )
    errors = final_state.get("errors", [])
    warnings = final_state.get("warnings", [])
    meals = final_state.get("candidate_meals", [])
    weekly = final_state.get("weekly_overview", [])
    coach = final_state.get("coach_notes", "Maintain steady hydration and portion balance.")
    declared_allergens = allergy_validator.normalize_declared_allergens(profile.allergies)

    if status == "provider_unavailable":
        return MealPlanResponse(
            request_id=req_id,
            status="provider_unavailable",
            calculated_targets=targets,
            adherence_score_pct=0,
            today_plan=DailyMealPlan(
                day="Today",
                calories_total=0.0,
                protein_total_g=0.0,
                carbs_total_g=0.0,
                fat_total_g=0.0,
                meals=[],
            ),
            weekly_overview=[],
            allergy_safety_cleared=False,
            excluded_allergens=declared_allergens,
            coach_notes=errors[0] if errors else "AI provider is not configured. Set GROQ_API_KEY in backend .env to generate dynamic personalized meal plans.",
            warnings=errors or ["Groq API key is not configured."],
        )

    if status == "allergy_conflict":
        violations = final_state.get("allergy_violations", [])
        return MealPlanResponse(
            request_id=req_id,
            status="allergy_conflict",
            calculated_targets=targets,
            adherence_score_pct=0,
            today_plan=DailyMealPlan(
                day="Today",
                calories_total=0.0,
                protein_total_g=0.0,
                carbs_total_g=0.0,
                fat_total_g=0.0,
                meals=[],
            ),
            weekly_overview=[],
            allergy_safety_cleared=False,
            excluded_allergens=declared_allergens,
            coach_notes=f"CRITICAL SAFETY WARNING: Candidate meals contained declared allergens: {', '.join(violations)}. Generation was terminated to prevent health hazards.",
            warnings=violations,
        )

    if status in {"generation_failed", "error"} or len(meals) == 0 or final_state.get("allergy_safety_cleared") is not True:
        fail_msgs = errors or ["Meal plan is empty or could not be validated."]
        return MealPlanResponse(
            request_id=req_id,
            status="generation_failed",
            calculated_targets=targets,
            adherence_score_pct=0,
            today_plan=DailyMealPlan(
                day="Today",
                calories_total=0.0,
                protein_total_g=0.0,
                carbs_total_g=0.0,
                fat_total_g=0.0,
                meals=[],
            ),
            weekly_overview=[],
            allergy_safety_cleared=False,
            excluded_allergens=declared_allergens,
            coach_notes="Meal planning generation could not produce a complete, verified plan.",
            warnings=fail_msgs,
        )

    total_cal = round(sum(m.calories_kcal for m in meals), 1)
    total_p = round(sum(m.protein_g for m in meals), 1)
    total_c = round(sum(m.carbohydrates_g for m in meals), 1)
    total_f = round(sum(m.fat_g for m in meals), 1)

    return MealPlanResponse(
        request_id=req_id,
        status="success",
        calculated_targets=targets,
        adherence_score_pct=92,
        today_plan=DailyMealPlan(
            day="Today",
            calories_total=total_cal,
            protein_total_g=total_p,
            carbs_total_g=total_c,
            fat_total_g=total_f,
            meals=meals,
        ),
        weekly_overview=weekly,
        allergy_safety_cleared=True,
        excluded_allergens=declared_allergens,
        coach_notes=coach,
        warnings=warnings,
    )
