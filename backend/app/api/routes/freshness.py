"""
FoodVerse AI — Freshness & Spoilage Route.

Analyzes food image with Groq Vision (qwen/qwen3.8-27b), validates outputs,
enforces deterministic safety thresholds, stores image in GridFS, and persists report.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES
from app.core.session import get_current_owner_id
from app.db.media_repository import media_repository
from app.db.report_repository import report_repository
from app.schemas.freshness import FreshnessAnalysisResponse
from app.services.freshness_service import freshness_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/freshness-analysis",
    response_model=FreshnessAnalysisResponse,
    summary="Analyze food freshness and spoilage risk using vision and context",
)
async def analyze_freshness(
    image: UploadFile = File(..., description="Food photo for visual quality and mold inspection"),
    food_name: Optional[str] = Form(None, description="Reported food item name"),
    storage_type: Optional[str] = Form("Room Temp", description="Storage condition: Room Temp, Refrigerator, Pantry"),
    storage_days: Optional[int] = Form(1, description="Number of days stored"),
    sensory_notes: Optional[str] = Form(None, description="Optional sensory observations (odor, texture)"),
    owner_id: str = Depends(get_current_owner_id),
) -> FreshnessAnalysisResponse:
    """Ingest image and storage context, returning structured visual freshness assessment."""
    if not image or not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_FILE", "message": "No file uploaded."}},
        )

    raw_bytes = await image.read()
    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_FILE", "message": "Uploaded image file is empty."}},
        )

    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB limit."}},
        )

    # Persist image to GridFS
    media_meta = await media_repository.upload_image(
        owner_id=owner_id,
        file_bytes=raw_bytes,
        filename=image.filename,
        feature="freshness_analysis",
    )
    media_id = media_meta.get("file_id") if media_meta else None
    media_url = f"/api/v1/media/{media_id}" if media_id else None

    # Execute vision freshness analysis
    result = freshness_service.analyze(
        image_bytes=raw_bytes,
        food_name=food_name,
        storage_type=storage_type,
        storage_days=storage_days,
        sensory_notes=sensory_notes,
    )

    result.media_id = media_id
    result.media_url = media_url

    # Persist report document
    report_doc = await report_repository.create_report(
        owner_id=owner_id,
        feature="freshness_analysis",
        status="completed" if result.status == "success" else "failed",
        input_data={
            "food_name": food_name,
            "storage_type": storage_type,
            "storage_days": storage_days,
            "sensory_notes": sensory_notes,
            "filename": image.filename,
        },
        result_data=result.model_dump(),
        media_refs=[{
            "file_id": media_id,
            "content_type": media_meta.get("content_type", "image/jpeg"),
            "role": "input_image",
        }] if media_id else [],
        model_info={
            "provider": "groq",
            "model_id": "qwen/qwen3.8-27b",
        },
        metrics={"confidence": result.confidence},
    )
    if report_doc:
        result.report_id = report_doc.get("id")

    return result
