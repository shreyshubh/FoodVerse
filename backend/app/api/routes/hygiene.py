"""
FoodVerse AI — Hygiene & Safety Monitor Route.

Inspects kitchen station image or video frames using local YOLOv8n PPE detector.
Persists the inspection report and image evidence (never large raw videos) in MongoDB.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import MAX_VIDEO_SIZE_BYTES
from app.core.session import get_current_owner_id
from app.db.media_repository import media_repository
from app.db.report_repository import report_repository
from app.schemas.hygiene import HygieneInspectionResponse
from app.services.hygiene_detector import hygiene_detector_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/hygiene-analysis",
    response_model=HygieneInspectionResponse,
    summary="Inspect kitchen station image or video for PPE compliance",
)
async def inspect_hygiene(
    media: UploadFile = File(..., description="CCTV video clip or snapshot photo"),
    station_id: Optional[str] = Form("Prep Line 01", description="Monitored station name"),
    owner_id: str = Depends(get_current_owner_id),
) -> HygieneInspectionResponse:
    """Run YOLO object and PPE detection on media, returning structured compliance report."""
    if not media or not media.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_FILE", "message": "No media file uploaded."}},
        )

    raw_bytes = await media.read()
    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_FILE", "message": "Uploaded media file is empty."}},
        )

    if len(raw_bytes) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_VIDEO_SIZE_BYTES // (1024*1024)} MB limit."}},
        )

    # Determine if file is video by extension or content-type
    ext = media.filename.lower().split(".")[-1] if "." in media.filename else ""
    is_video = ext in {"mp4", "avi", "mov", "mkv", "webm"} or (media.content_type and "video" in media.content_type)

    # If it is an image (not video), upload to GridFS as evidence
    media_refs: List[dict] = []
    evidence_ids: List[str] = []
    if not is_video:
        media_meta = await media_repository.upload_image(
            owner_id=owner_id,
            file_bytes=raw_bytes,
            filename=media.filename,
            feature="hygiene_analysis",
        )
        if media_meta:
            media_refs.append({
                "file_id": media_meta["file_id"],
                "content_type": media_meta.get("content_type", "image/jpeg"),
                "role": "station_snapshot",
            })
            evidence_ids.append(media_meta["file_id"])

    # Run YOLO PPE detector
    result = hygiene_detector_service.inspect_media(
        media_bytes=raw_bytes,
        is_video=is_video,
        station_id=station_id or "Station 01",
    )
    result.evidence_media_ids = evidence_ids

    # Persist inspection report
    report_doc = await report_repository.create_report(
        owner_id=owner_id,
        feature="hygiene_analysis",
        status="completed" if result.status in {"success", "no_person_detected", "not_assessable"} else "failed",
        input_data={
            "station_id": station_id,
            "filename": media.filename,
            "is_video": is_video,
        },
        result_data=result.model_dump(),
        media_refs=media_refs,
        model_info={
            "provider": "local_ultralytics_yolo",
            "model_id": "yolov8n-ppe",
            "version": "1.0.0",
        },
        metrics={
            "overall_score": result.overall_score,
            "risk_level": result.risk_level,
            "persons_observed": result.persons_observed,
            "frames_analyzed": result.frames_analyzed,
            "violations_count": len(result.alerts),
        },
    )
    if report_doc:
        result.report_id = report_doc.get("id")

    return result
