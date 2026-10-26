"""
FoodVerse AI — GridFS Media Access API Route.

Streams validated images from foodverse_media bucket with strict owner isolation.
"""
from __future__ import annotations

import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from starlette.responses import StreamingResponse

from app.core.session import get_current_owner_id
from app.db.media_repository import media_repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/media/{file_id}", summary="Stream uploaded image from GridFS")
async def get_media_file(
    file_id: str,
    owner_id: str = Depends(get_current_owner_id),
) -> Response:
    """
    Streams an image file from GridFS bucket foodverse_media.
    Ownership is strictly verified: only the owner who uploaded the image can retrieve it.
    Returns 404 if file does not exist or owner does not match.
    """
    media_data = await media_repository.get_image(file_id_str=file_id, owner_id=owner_id)
    if not media_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Media file not found or access denied."},
        )

    file_bytes, content_type, filename = media_data

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "private, max-age=86400",  # Safe private caching for 1 day
        "X-Content-Type-Options": "nosniff",
    }

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=content_type,
        headers=headers,
    )
