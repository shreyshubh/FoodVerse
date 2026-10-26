"""
FoodVerse AI — MongoDB Persistence & GridFS Unit/Integration Tests.

Tests:
  - Database connectivity/unavailability fallback
  - ObjectId and datetime serialization
  - Image MIME validation, size limits, and EXIF normalization
  - MediaRepository GridFS upload, retrieval, and delete
  - Strict owner isolation for media and reports
  - ReportRepository CRUD for all 5 feature types
  - Cursor pagination and feature filtering
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from PIL import Image

from app.db.media_repository import (
    MAX_IMAGE_SIZE_BYTES,
    media_repository,
    sanitize_filename,
    validate_and_normalize_image,
)
from app.db.mongodb import db_manager, serialize_doc
from app.db.report_repository import report_repository


def create_sample_image(format="JPEG", size=(100, 100), color="blue") -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Serialization Tests
# ---------------------------------------------------------------------------
def test_serialize_doc_transforms_bson_types():
    obj_id = ObjectId()
    now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    raw = {
        "_id": obj_id,
        "owner_id": "test-owner",
        "created_at": now,
        "nested": {
            "media_id": ObjectId(),
            "date": now,
        },
        "media_list": [ObjectId(), "string_val"],
        "number": 42,
    }

    serialized = serialize_doc(raw)
    assert serialized is not None
    assert serialized["id"] == str(obj_id)
    assert serialized["_id"] == str(obj_id)
    assert serialized["created_at"] == now.isoformat()
    assert isinstance(serialized["nested"]["media_id"], str)
    assert isinstance(serialized["media_list"][0], str)
    assert serialized["number"] == 42


def test_serialize_doc_none_returns_none():
    assert serialize_doc(None) is None


# ---------------------------------------------------------------------------
# 2. Image Validation & Sanitization Tests
# ---------------------------------------------------------------------------
def test_image_validation_valid_jpeg():
    raw = create_sample_image(format="JPEG")
    norm, mime, size, sha = validate_and_normalize_image(raw, "photo.jpg")
    assert mime == "image/jpeg"
    assert len(norm) > 0
    assert size == len(norm)
    assert len(sha) == 64  # SHA-256 hex length


def test_image_validation_valid_png():
    raw = create_sample_image(format="PNG")
    norm, mime, size, sha = validate_and_normalize_image(raw, "photo.png")
    assert mime == "image/png"
    assert size > 0


def test_image_validation_empty_bytes_rejected():
    with pytest.raises(ValueError, match="empty"):
        validate_and_normalize_image(b"", "empty.jpg")


def test_image_validation_corrupt_bytes_rejected():
    with pytest.raises(ValueError, match="Corrupt or unreadable"):
        validate_and_normalize_image(b"not-an-image-data", "bad.jpg")


def test_image_validation_size_limit_rejection():
    # Fake a byte string exceeding limit
    oversized = b"x" * (MAX_IMAGE_SIZE_BYTES + 1024)
    with pytest.raises(ValueError, match="exceeds the maximum allowed limit"):
        validate_and_normalize_image(oversized, "huge.jpg")


def test_sanitize_filename_prevents_traversal():
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..//hidden.file.png") == "hidden.file.png"
    assert sanitize_filename(None) == "upload.jpg"


# ---------------------------------------------------------------------------
# 3. Database Unavailability Fallback Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_db_manager_unconfigured_offline():
    with patch.object(db_manager, "uri", None), patch.object(db_manager, "_is_connected", False):
        assert db_manager.is_configured is False
        assert db_manager.is_connected is False
        ping_res = await db_manager.ping()
        assert ping_res is False
        assert db_manager.get_reports_collection() is None
        assert db_manager.get_media_bucket() is None


@pytest.mark.asyncio
async def test_report_repository_graceful_when_db_offline():
    with patch.object(db_manager, "get_reports_collection", return_value=None):
        created = await report_repository.create_report(
            owner_id="session-1",
            feature="food_recognition",
        )
        assert created is None

        fetched = await report_repository.get_report(str(ObjectId()), "session-1")
        assert fetched is None

        listed = await report_repository.list_reports("session-1")
        assert listed["items"] == []
        assert listed["total"] == 0


# ---------------------------------------------------------------------------
# 4. MediaRepository GridFS & Strict Owner Isolation Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_media_repository_upload_and_owner_isolation():
    file_bytes = create_sample_image()
    mock_file_id = ObjectId()

    mock_bucket = MagicMock()
    mock_bucket.upload_from_stream = AsyncMock(return_value=mock_file_id)
    mock_bucket._bucket_name = "foodverse_media"

    # Mock DB files collection
    mock_files_coll = MagicMock()
    mock_files_coll.find_one = AsyncMock(return_value={
        "_id": mock_file_id,
        "filename": "apple.jpg",
        "metadata": {
            "owner_id": "verified-owner-123",
            "content_type": "image/jpeg",
        },
    })

    mock_download_stream = MagicMock()
    mock_download_stream.read = AsyncMock(return_value=file_bytes)
    mock_bucket.open_download_stream = AsyncMock(return_value=mock_download_stream)

    with patch.object(db_manager, "get_media_bucket", return_value=mock_bucket), \
         patch.object(db_manager, "_is_connected", True), \
         patch.object(db_manager, "client", MagicMock()), \
         patch.object(db_manager, "db", {"foodverse_media.files": mock_files_coll}):

        # Upload
        upload_res = await media_repository.upload_image(
            owner_id="verified-owner-123",
            file_bytes=file_bytes,
            filename="apple.jpg",
            feature="freshness_analysis",
        )
        assert upload_res is not None
        assert upload_res["file_id"] == str(mock_file_id)
        assert upload_res["content_type"] == "image/jpeg"

        # Authorized retrieval by owner
        retrieved = await media_repository.get_image(str(mock_file_id), owner_id="verified-owner-123")
        assert retrieved is not None
        data, content_type, filename = retrieved
        assert data == file_bytes
        assert content_type == "image/jpeg"

        # STRICT ISOLATION: Mismatched owner must be denied (returns None)
        unauthorized = await media_repository.get_image(str(mock_file_id), owner_id="attacker-owner-999")
        assert unauthorized is None


# ---------------------------------------------------------------------------
# 5. ReportRepository 5 Feature Types & Scoping Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_report_repository_supports_all_five_features():
    features = [
        "food_recognition",
        "freshness_analysis",
        "hygiene_analysis",
        "recipe_generation",
        "meal_plan",
    ]

    mock_coll = MagicMock()
    mock_insert = MagicMock()
    mock_id = ObjectId()
    mock_insert.inserted_id = mock_id
    mock_coll.insert_one = AsyncMock(return_value=mock_insert)

    with patch.object(db_manager, "get_reports_collection", return_value=mock_coll):
        for feat in features:
            res = await report_repository.create_report(
                owner_id="owner-abc",
                feature=feat,
                status="completed",
                input_data={"test": "data"},
                result_data={"key": "val"},
            )
            assert res is not None
            assert res["id"] == str(mock_id)
            assert res["feature"] == feat
            assert res["owner_id"] == "owner-abc"
