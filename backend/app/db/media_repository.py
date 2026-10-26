"""
FoodVerse AI — GridFS Media Repository & Image Sanitization Layer.

Handles upload, validation, EXIF stripping, SHA-256 calculation,
and strictly owner-scoped download/delete for the foodverse_media bucket.
"""
from __future__ import annotations

import hashlib
import io
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from bson import ObjectId
from PIL import Image

from app.db.mongodb import db_manager

logger = logging.getLogger(__name__)

# Upload configuration
ALLOWED_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
MIN_DIMENSION = 10
MAX_DIMENSION = 4096


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize filename to prevent directory traversal or malformed characters."""
    if not filename:
        return "upload.jpg"
    import os
    # Take basename across Windows and POSIX separators
    base = os.path.basename(filename.replace("\\", "/"))
    # Keep only alphanumeric, hyphen, underscore, and dot
    clean = re.sub(r"[^\w\.\-]", "_", base.strip())
    # Prevent hidden files and leading dots/underscores
    clean = clean.lstrip("._")
    return clean[:100] or "upload.jpg"


def validate_and_normalize_image(
    file_bytes: bytes,
    original_filename: Optional[str] = None,
) -> Tuple[bytes, str, int, str]:
    """
    Validate raw file bytes:
    - Check size <= MAX_IMAGE_SIZE_BYTES
    - Verify actual image content and supported format with PIL
    - Verify dimensions
    - Strip EXIF metadata to prevent privacy leaks and normalize format
    - Compute SHA-256 checksum

    Returns: (normalized_bytes, mime_type, size_bytes, sha256_hex)
    Raises ValueError on invalid upload.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError(
            f"File size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of {MAX_IMAGE_SIZE_BYTES} bytes (10MB)."
        )

    # Decode with Pillow
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            format_name = (img.format or "").upper()
            if format_name not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError(f"Unsupported image format '{format_name}'. Allowed formats: JPEG, PNG, WEBP.")

            width, height = img.size
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise ValueError(f"Image dimensions ({width}x{height}) are too small. Minimum is {MIN_DIMENSION}x{MIN_DIMENSION}px.")
            if width > MAX_DIMENSION or height > MAX_DIMENSION:
                raise ValueError(f"Image dimensions ({width}x{height}) exceed maximum allowed {MAX_DIMENSION}x{MAX_DIMENSION}px.")

            # Re-encode to strip EXIF and normalize
            out_buf = io.BytesIO()
            if format_name in {"JPEG", "JPG"}:
                # Convert RGBA to RGB for JPEG
                if img.mode in ("RGBA", "P"):
                    rgb_img = img.convert("RGB")
                    rgb_img.save(out_buf, format="JPEG", quality=90, optimize=True)
                else:
                    img.save(out_buf, format="JPEG", quality=90, optimize=True)
                mime_type = "image/jpeg"
            elif format_name == "PNG":
                img.save(out_buf, format="PNG", optimize=True)
                mime_type = "image/png"
            elif format_name == "WEBP":
                img.save(out_buf, format="WEBP", quality=90)
                mime_type = "image/webp"
            else:
                img.save(out_buf, format="JPEG", quality=90)
                mime_type = "image/jpeg"

            normalized_bytes = out_buf.getvalue()
    except ValueError:
        raise
    except Exception as exc:
        logger.warning("Image decoding validation failed: %s", exc)
        raise ValueError(f"Corrupt or unreadable image file: {str(exc)}")

    sha256_hash = hashlib.sha256(normalized_bytes).hexdigest()
    return normalized_bytes, mime_type, len(normalized_bytes), sha256_hash


class MediaRepository:
    """Manages uploads, downloads, and deletions in the GridFS foodverse_media bucket."""

    async def upload_image(
        self,
        owner_id: str,
        file_bytes: bytes,
        filename: Optional[str] = None,
        feature: str = "food_recognition",
        report_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Validate, normalize, and upload an image to GridFS bucket.
        Returns metadata dict including file_id (str) or None if database is unavailable.
        """
        bucket = db_manager.get_media_bucket()
        if bucket is None:
            logger.debug("Database not connected. Skipping GridFS upload.")
            return None

        # Validate and strip EXIF
        norm_bytes, mime_type, size, sha256_hex = validate_and_normalize_image(
            file_bytes, original_filename=filename
        )
        clean_name = sanitize_filename(filename)

        meta = {
            "owner_id": owner_id,
            "report_id": report_id,
            "feature": feature,
            "filename": clean_name,
            "content_type": mime_type,
            "size_bytes": size,
            "sha256": sha256_hex,
            "uploaded_at": datetime.now(timezone.utc),
        }

        try:
            # Upload stream to GridFS
            file_id = await bucket.upload_from_stream(
                filename=clean_name,
                source=norm_bytes,
                metadata=meta,
            )
            logger.info("Uploaded image to GridFS: file_id=%s, owner=%s", str(file_id), owner_id)
            return {
                "file_id": str(file_id),
                "content_type": mime_type,
                "filename": clean_name,
                "size_bytes": size,
                "sha256": sha256_hex,
            }
        except Exception as exc:
            logger.error("Failed to upload image to GridFS: %s", exc)
            return None

    async def get_image(
        self,
        file_id_str: str,
        owner_id: str,
    ) -> Optional[Tuple[bytes, str, str]]:
        """
        Retrieve an image from GridFS strictly scoped to the verified owner_id.
        Returns: (file_bytes, content_type, filename) or None if not found or unauthorized.
        """
        bucket = db_manager.get_media_bucket()
        if bucket is None:
            return None

        try:
            file_id = ObjectId(file_id_str)
        except Exception:
            return None

        try:
            # Find file document in files collection to verify ownership
            files_coll = db_manager.db[f"{bucket._bucket_name}.files"]
            file_doc = await files_coll.find_one({"_id": file_id})
            if not file_doc:
                return None

            metadata = file_doc.get("metadata", {})
            # STRICT OWNER ISOLATION:
            if metadata.get("owner_id") != owner_id:
                logger.warning(
                    "Unauthorized media access attempt: file_id=%s belongs to owner %s, requested by %s",
                    file_id_str,
                    metadata.get("owner_id"),
                    owner_id,
                )
                return None

            content_type = metadata.get("content_type", "image/jpeg")
            filename = file_doc.get("filename", "image.jpg")

            # Stream bytes out
            grid_out = await bucket.open_download_stream(file_id)
            data = await grid_out.read()
            return data, content_type, filename
        except Exception as exc:
            logger.error("Error retrieving media from GridFS: %s", exc)
            return None

    async def delete_image(self, file_id_str: str, owner_id: str) -> bool:
        """Delete an image from GridFS if owned by owner_id."""
        bucket = db_manager.get_media_bucket()
        if bucket is None:
            return False

        try:
            file_id = ObjectId(file_id_str)
            files_coll = db_manager.db[f"{bucket._bucket_name}.files"]
            file_doc = await files_coll.find_one({"_id": file_id})
            if not file_doc:
                return False

            if file_doc.get("metadata", {}).get("owner_id") != owner_id:
                return False

            await bucket.delete(file_id)
            logger.info("Deleted GridFS file %s for owner %s", file_id_str, owner_id)
            return True
        except Exception as exc:
            logger.warning("Failed to delete GridFS image %s: %s", file_id_str, exc)
            return False


media_repository = MediaRepository()
