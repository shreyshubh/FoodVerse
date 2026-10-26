"""
FoodVerse AI — Smart Kitchen Recipe Generation Route.

Runs LangGraph recipe workflow via Groq openai/gpt-oss-120b.
Persists recipe reports and optional pantry images in MongoDB.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.agents.recipe_graph import execute_recipe_generation
from app.core.config import MAX_UPLOAD_SIZE_BYTES
from app.core.session import get_current_owner_id
from app.db.media_repository import media_repository
from app.db.report_repository import report_repository
from app.schemas.recipes import RecipeResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/recipes/generate",
    response_model=RecipeResponse,
    summary="Generate authentic recipe using LangGraph agent and Groq LLM",
)
async def generate_recipe(
    ingredients_text: str = Form(..., description="Available ingredients or natural language dish description"),
    servings: Optional[int] = Form(2, description="Target number of servings"),
    cuisine: Optional[str] = Form(None, description="Preferred cuisine style"),
    dietary_restrictions: Optional[str] = Form(None, description="Comma-separated dietary constraints"),
    image: Optional[UploadFile] = File(None, description="Optional pantry/ingredients snapshot"),
    owner_id: str = Depends(get_current_owner_id),
) -> RecipeResponse:
    """Run LangGraph recipe generation graph with schema and dietary verification."""
    if not ingredients_text.strip() and not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "MISSING_INPUT", "message": "Please provide an ingredient description or image."}},
        )

    image_bytes = None
    media_meta = None
    if image and image.filename:
        raw = await image.read()
        if len(raw) > 0:
            if len(raw) > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={"error": {"code": "FILE_TOO_LARGE", "message": "Image exceeds size limit."}},
                )
            image_bytes = raw
            media_meta = await media_repository.upload_image(
                owner_id=owner_id,
                file_bytes=raw,
                filename=image.filename,
                feature="recipe_generation",
            )

    dietary_list = [d.strip() for d in dietary_restrictions.split(",") if d.strip()] if dietary_restrictions else []

    response = execute_recipe_generation(
        ingredients_text=ingredients_text,
        image_bytes=image_bytes,
        dietary_restrictions=dietary_list,
        cuisine=cuisine,
        servings=servings or 2,
    )

    # Persist report
    report_doc = await report_repository.create_report(
        owner_id=owner_id,
        feature="recipe_generation",
        status="completed" if response.status == "success" else "failed",
        input_data={
            "ingredients_text": ingredients_text,
            "servings": servings or 2,
            "cuisine": cuisine,
            "dietary_restrictions": dietary_list,
        },
        result_data=response.model_dump(),
        media_refs=[{
            "file_id": media_meta["file_id"],
            "content_type": media_meta.get("content_type", "image/jpeg"),
            "role": "pantry_input",
        }] if media_meta else [],
        model_info={
            "provider": "groq",
            "model_id": "openai/gpt-oss-120b",
        },
        metrics={
            "prep_time_minutes": response.prep_time_minutes,
            "cook_time_minutes": response.cook_time_minutes,
            "servings": response.servings,
        },
    )
    if report_doc:
        response.report_id = report_doc.get("id")

    return response
