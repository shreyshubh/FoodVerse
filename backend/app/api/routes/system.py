"""
FoodVerse AI — System Health & Deep Readiness Probes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.groq_provider import groq_provider
from app.db.mongodb import db_manager
from app.repositories.nutrition_repository import nutrition_repository
from app.services.food_recognition import food_recognition_service
from app.services.hygiene_detector import hygiene_detector_service

router = APIRouter()


@router.get("/health", tags=["System"])
async def liveness_probe() -> Dict[str, Any]:
    """Liveness probe: verifies that the FastAPI application event loop is running."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "food_recognition": "ready" if food_recognition_service.is_ready else "unavailable",
            "nutrition_reference": "ready" if nutrition_repository.is_ready else "unavailable",
            "hygiene_detector": "ready" if hygiene_detector_service.is_ready else "unavailable",
            "groq_provider": "configured" if groq_provider.is_available else "not_configured",
            "database": "connected" if db_manager.is_connected else ("unconfigured" if not db_manager.is_configured else "offline"),
        },
    }


@router.get("/ready", tags=["System"])
async def readiness_probe() -> Dict[str, Any]:
    """
    Deep readiness probe: verifies all local neural checkpoints,
    database connectivity, and external AI provider configurations.
    Does not claim a provider is live merely because a key is present.
    """
    models_ready = {
        "mobilenetv2_food101": food_recognition_service.is_ready,
        "yolov8n_ppe": hygiene_detector_service.is_ready,
        "usda_nutrition_db": nutrition_repository.is_ready,
        "groq_configured": groq_provider.is_available,
    }

    db_ping_ok = await db_manager.ping()

    # Core local models must be operational for baseline readiness
    is_core_ready = models_ready["mobilenetv2_food101"] and models_ready["usda_nutrition_db"]
    overall_status = "ready" if (is_core_ready and models_ready["yolov8n_ppe"]) else ("degraded" if is_core_ready else "unavailable")

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": {
            "food_recognition": "loaded" if models_ready["mobilenetv2_food101"] else "unloaded",
            "hygiene_detector": "loaded" if models_ready["yolov8n_ppe"] else "unloaded",
            "nutrition_reference": "loaded" if models_ready["usda_nutrition_db"] else "unloaded",
        },
        "database": {
            "configured": db_manager.is_configured,
            "connected": db_ping_ok,
            "status": "connected" if db_ping_ok else ("not_configured" if not db_manager.is_configured else "unreachable"),
        },
        "external_providers": {
            "groq_ai": {
                "configured": models_ready["groq_configured"],
                "text_model": groq_provider.text_model,
                "vision_model": groq_provider.vision_model,
                "status": "configured" if models_ready["groq_configured"] else "not_configured (GROQ_API_KEY missing)",
            },
        },
        "orchestration": {
            "smart_kitchen_graph": "compiled (LangGraph Groq openai/gpt-oss-120b)",
            "meal_planner_graph": "compiled (LangGraph Groq openai/gpt-oss-120b)",
        },
    }
