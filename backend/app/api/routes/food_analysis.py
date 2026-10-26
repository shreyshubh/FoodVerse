"""
FoodVerse AI — Food analysis API route.

POST /api/v1/food-analysis

Handles multipart image upload, validation, model inference,
nutrition estimation, and structured response/error serialization.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    CONFIDENCE_THRESHOLD,
    MAX_UPLOAD_SIZE_BYTES,
)
from app.core.session import get_current_owner_id
from app.db.media_repository import media_repository
from app.db.report_repository import report_repository
from app.schemas.food_analysis import (
    ApiErrorDetail,
    ApiErrorResponse,
    FoodAnalysisResponse,
    FoodPrediction,
)
from app.services.food_recognition import (
    ModelUnavailableError,
    food_recognition_service,
)
from app.services.image_processing import (
    ImageValidationError,
    decode_image,
    preprocess_for_model,
    validate_image_dimensions,
)
from app.services.nutrition_estimation import (
    compute_health_score,
    estimate_nutrition,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/food-analysis",
    response_model=FoodAnalysisResponse,
    responses={
        400: {"model": ApiErrorResponse, "description": "Invalid request"},
        413: {"model": ApiErrorResponse, "description": "File too large"},
        415: {"model": ApiErrorResponse, "description": "Unsupported media type"},
        422: {"model": ApiErrorResponse, "description": "Image decode/validation failure"},
        503: {"model": ApiErrorResponse, "description": "Model unavailable"},
    },
    summary="Analyze a food image",
    description="Upload a food image for recognition and nutrition estimation.",
)
async def analyze_food(
    image: UploadFile = File(..., description="Food image file"),
    serving_grams: float | None = Form(
        default=None,
        description="Optional user-confirmed serving size in grams",
    ),
    owner_id: str = Depends(get_current_owner_id),
):
    """
    Full food analysis pipeline:
    1. Validate upload metadata (size, extension, MIME)
    2. Read and validate image bytes (decode, dimensions)
    3. Preprocess for model
    4. Run food recognition
    5. Estimate nutrition from prediction
    6. Persist image to GridFS and report to MongoDB
    7. Return structured response with assumptions/warnings
    """
    request_id = str(uuid.uuid4())

    try:
        # --- Step 1: Validate upload metadata ---
        _validate_upload_metadata(image, request_id)

        # --- Step 2: Read and validate image bytes ---
        file_bytes = await image.read()

        if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
            _raise_error(
                413,
                "FILE_TOO_LARGE",
                f"File size exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB limit.",
                request_id,
            )

        if len(file_bytes) == 0:
            _raise_error(400, "EMPTY_FILE", "Uploaded file is empty.", request_id)

        decoded = decode_image(file_bytes)
        validate_image_dimensions(decoded)

        # Persist raw image to GridFS foodverse_media bucket
        media_meta = await media_repository.upload_image(
            owner_id=owner_id,
            file_bytes=file_bytes,
            filename=image.filename,
            feature="food_recognition",
        )
        media_id = media_meta.get("file_id") if media_meta else None
        media_url = f"/api/v1/media/{media_id}" if media_id else None

        # --- Step 3: Preprocess for model ---
        preprocessed = preprocess_for_model(decoded)

        # --- Step 4: Food recognition ---
        prediction_result = food_recognition_service.predict(preprocessed)

        # Build prediction schema
        prediction = FoodPrediction(
            label=prediction_result.label,
            confidence=prediction_result.confidence,
            canonical_food_id=prediction_result.canonical_food_id,
        )

        # Determine analysis status
        if prediction_result.confidence < 0.25:
            status = "inconclusive"
        elif prediction_result.needs_confirmation:
            status = "needs_confirmation"
        else:
            status = "success"

        # --- Step 5: Nutrition estimation ---
        # Validate serving_grams
        if serving_grams is not None:
            if serving_grams <= 0 or not _is_finite(serving_grams):
                _raise_error(
                    400,
                    "INVALID_SERVING",
                    "Serving size must be a positive number.",
                    request_id,
                )

        nutrition, assumptions, warnings = estimate_nutrition(
            canonical_food_id=prediction_result.canonical_food_id,
            serving_grams=serving_grams,
        )

        # Add confidence / uncertainty warnings
        if status == "inconclusive":
            warnings.insert(
                0,
                f"Low confidence ({prediction_result.confidence:.1%}). "
                "The dish appears outside the currently supported Food-101 catalog. "
                "Nutritional estimates should be verified manually.",
            )
        elif status == "needs_confirmation":
            warnings.insert(
                0,
                f"Low confidence ({prediction_result.confidence:.1%}). "
                "The predicted food may be incorrect — please verify.",
            )

        # Add alternatives info
        if prediction_result.alternatives:
            alt_labels = [a["label"] for a in prediction_result.alternatives[:3]]
            assumptions.append(
                f"Other possible foods: {', '.join(alt_labels)}."
            )

        # --- Step 6: Health score (always unavailable in v1) ---
        health_score = compute_health_score()

        resp_obj = FoodAnalysisResponse(
            request_id=request_id,
            status=status,
            prediction=prediction,
            nutrition=nutrition,
            health_score=health_score,
            assumptions=assumptions,
            warnings=warnings,
            media_id=media_id,
            media_url=media_url,
        )

        # --- Step 7: Persist report to MongoDB ---
        report_doc = await report_repository.create_report(
            owner_id=owner_id,
            feature="food_recognition",
            status="completed" if status in {"success", "needs_confirmation", "inconclusive"} else "failed",
            input_data={
                "filename": image.filename,
                "serving_grams": serving_grams,
            },
            result_data={
                "predicted_food": prediction.label,
                "confidence": prediction.confidence,
                "status": status,
                "nutrition": nutrition.model_dump() if nutrition else {},
            },
            media_refs=[{
                "file_id": media_id,
                "content_type": media_meta.get("content_type", "image/jpeg"),
                "role": "input_image",
            }] if media_id else [],
            model_info={
                "provider": "local_pytorch",
                "model_id": "mobilenetv2_food101",
                "version": "1.0.0",
            },
            metrics={
                "confidence": prediction_result.confidence,
            },
        )
        if report_doc:
            resp_obj.report_id = report_doc.get("id")

        return resp_obj

    except HTTPException:
        raise

    except ImageValidationError as exc:
        logger.warning("Image validation failed [%s]: %s", request_id, exc.message)
        _raise_error(422, exc.code, exc.message, request_id)

    except ModelUnavailableError as exc:
        logger.warning("Model unavailable [%s]: %s", request_id, exc.message)
        safe_msg = "Food recognition model is currently unavailable. Please provide trained model weights."
        _raise_error(503, "MODEL_UNAVAILABLE", safe_msg, request_id)

    except Exception as exc:
        logger.error(
            "Unexpected error during food analysis [%s]: %s",
            request_id,
            exc,
            exc_info=True,
        )
        _raise_error(
            500,
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again later.",
            request_id,
        )


def _validate_upload_metadata(image: UploadFile, request_id: str) -> None:
    """Validate file extension and MIME type before reading bytes."""
    filename = image.filename or ""
    ext = Path(filename).suffix.lower()

    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        _raise_error(
            415,
            "UNSUPPORTED_FORMAT",
            f"File type '{ext}' is not supported. Please upload a JPEG, PNG, or WebP image.",
            request_id,
        )

    content_type = image.content_type or ""
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        _raise_error(
            415,
            "UNSUPPORTED_MEDIA_TYPE",
            f"Media type '{content_type}' is not supported. Please upload a JPEG, PNG, or WebP image.",
            request_id,
        )


def _raise_error(status_code: int, code: str, message: str, request_id: str) -> None:
    """Raise an HTTPException with our standard error envelope."""
    raise HTTPException(
        status_code=status_code,
        detail=ApiErrorResponse(
            error=ApiErrorDetail(
                code=code,
                message=message,
                request_id=request_id,
            )
        ).model_dump(),
    )


def _is_finite(value: float) -> bool:
    """Check if a float is finite (not NaN or Inf)."""
    import math
    return math.isfinite(value)
