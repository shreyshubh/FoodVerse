"""
FoodVerse AI — FastAPI application entry point.

Registers routers, configures CORS, and initializes services and MongoDB at startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.food_analysis import router as food_analysis_router
from app.api.routes.freshness import router as freshness_router
from app.api.routes.history import router as history_router
from app.api.routes.hygiene import router as hygiene_router
from app.api.routes.meal_planner import router as meal_planner_router
from app.api.routes.media import router as media_router
from app.api.routes.recipes import router as recipes_router
from app.api.routes.system import router as system_router
from app.core.config import API_V1_PREFIX, CORS_ORIGINS, LOG_LEVEL
from app.core.groq_provider import groq_provider
from app.db.mongodb import db_manager
from app.repositories.nutrition_repository import nutrition_repository
from app.services.food_recognition import food_recognition_service
from app.services.hygiene_detector import hygiene_detector_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: initialize neural models, external providers,
    and MongoDB connection pool at startup.
    """
    logger.info("FoodVerse AI starting up...")

    # 1. Initialize food recognition MobileNetV2 model
    food_recognition_service.initialize()
    if food_recognition_service.is_ready:
        logger.info("Food recognition model (MobileNetV2): READY")
    else:
        logger.warning("Food recognition model: UNAVAILABLE")

    # 2. Initialize USDA nutrition reference
    nutrition_repository.initialize()
    if nutrition_repository.is_ready:
        logger.info("Nutrition reference (USDA): READY")
    else:
        logger.warning("Nutrition reference: UNAVAILABLE")

    # 3. Initialize YOLO PPE detector
    hygiene_detector_service.initialize()
    if hygiene_detector_service.is_ready:
        logger.info("Hygiene detector (YOLOv8n-PPE): READY")
    else:
        logger.warning("Hygiene detector: UNAVAILABLE")

    # 4. Check Groq Multimodal Provider
    if groq_provider.is_available:
        logger.info(
            "Groq AI Provider: CONFIGURED (Text: %s, Vision: %s)",
            groq_provider.text_model,
            groq_provider.vision_model,
        )
    else:
        logger.info("Groq AI Provider: RUNNING OFFLINE (GROQ_API_KEY not set)")

    # 5. Connect to MongoDB Atlas / Local MongoDB
    await db_manager.connect()

    yield

    # Shutdown
    await db_manager.disconnect()
    logger.info("FoodVerse AI shutting down.")


app = FastAPI(
    title="FoodVerse AI",
    description="Comprehensive AI-powered Food Recognition, Freshness, Hygiene, Recipe, and Nutrition Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — Support local development, custom origins, and all Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router, prefix=f"{API_V1_PREFIX}", tags=["Authentication"])
app.include_router(food_analysis_router, prefix=f"{API_V1_PREFIX}", tags=["Food Analysis"])
app.include_router(freshness_router, prefix=f"{API_V1_PREFIX}", tags=["Freshness Detector"])
app.include_router(hygiene_router, prefix=f"{API_V1_PREFIX}", tags=["Hygiene Monitor"])
app.include_router(recipes_router, prefix=f"{API_V1_PREFIX}", tags=["Smart Kitchen"])
app.include_router(meal_planner_router, prefix=f"{API_V1_PREFIX}", tags=["Meal Planner"])
app.include_router(history_router, prefix=f"{API_V1_PREFIX}", tags=["History"])
app.include_router(media_router, prefix=f"{API_V1_PREFIX}", tags=["Media"])
app.include_router(system_router, tags=["System"])
