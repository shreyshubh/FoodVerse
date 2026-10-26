"""
FoodVerse AI — Centralized MongoDB Database & GridFS Layer.

Uses official PyMongo asynchronous API (AsyncMongoClient) and AsyncGridFSBucket.
No Motor dependency.
Handles lifecycle, ping, indexes, collections, and safe BSON serialization.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from gridfs import AsyncGridFSBucket
from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from app.core.config import (
    GRIDFS_MEDIA_BUCKET,
    MONGODB_DATABASE,
    MONGODB_URI,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages AsyncMongoClient, GridFS bucket, and index lifecycles."""

    def __init__(self) -> None:
        self.uri: Optional[str] = MONGODB_URI
        self.db_name: str = MONGODB_DATABASE
        self.client: Optional[AsyncMongoClient] = None
        self.db = None
        self.media_bucket: Optional[AsyncGridFSBucket] = None
        self._is_connected: bool = False

    @property
    def is_configured(self) -> bool:
        """True if MONGODB_URI is provided."""
        return bool(self.uri and self.uri.strip())

    @property
    def is_connected(self) -> bool:
        """True if the client is connected and validated."""
        return self._is_connected and self.client is not None

    async def connect(self) -> bool:
        """
        Connect to MongoDB Atlas or local MongoDB using PyMongo AsyncMongoClient.
        Creates required compound indexes.
        """
        if not self.is_configured:
            logger.info("MongoDB: MONGODB_URI is not set. Running in database-offline mode.")
            self._is_connected = False
            return False

        try:
            logger.info("Connecting to MongoDB database '%s'...", self.db_name)
            self.client = AsyncMongoClient(
                self.uri.strip(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            self.db = self.client[self.db_name]
            self.media_bucket = AsyncGridFSBucket(self.db, bucket_name=GRIDFS_MEDIA_BUCKET)

            # Test connection with ping command
            await self.db.command("ping")
            self._is_connected = True
            logger.info("MongoDB connection successful: ping OK.")

            # Ensure indexes asynchronously
            await self._ensure_indexes()
            return True
        except (ServerSelectionTimeoutError, ConnectionFailure, PyMongoError, Exception) as exc:
            logger.warning("MongoDB connection failed (%s). Continuing in offline mode.", exc)
            self._is_connected = False
            self.client = None
            self.db = None
            self.media_bucket = None
            return False

    async def disconnect(self) -> None:
        """Close AsyncMongoClient connection."""
        if self.client:
            logger.info("Closing MongoDB client connection...")
            try:
                await self.client.close()
            except Exception as exc:
                logger.warning("Error while closing MongoDB client: %s", exc)
            finally:
                self.client = None
                self.db = None
                self.media_bucket = None
                self._is_connected = False

    async def ping(self) -> bool:
        """Ping MongoDB to verify active connectivity."""
        if not self.is_connected or self.db is None:
            return False
        try:
            await self.db.command("ping")
            return True
        except Exception as exc:
            logger.debug("MongoDB ping failed: %s", exc)
            return False

    async def _ensure_indexes(self) -> None:
        """Create compound indexes for owner-scoped queries and media lookups."""
        if self.db is None:
            return

        try:
            reports_coll = self.db["analysis_reports"]
            # 1. Owner + Created_At descending (primary history feed)
            await reports_coll.create_index(
                [("owner_id", 1), ("created_at", -1)],
                name="idx_owner_created_at",
            )
            # 2. Owner + Feature + Created_At descending (feature filtering)
            await reports_coll.create_index(
                [("owner_id", 1), ("feature", 1), ("created_at", -1)],
                name="idx_owner_feature_created_at",
            )
            # 3. Owner + Status + Created_At descending (status filtering)
            await reports_coll.create_index(
                [("owner_id", 1), ("status", 1), ("created_at", -1)],
                name="idx_owner_status_created_at",
            )

            # GridFS files collection indexes
            files_coll = self.db[f"{GRIDFS_MEDIA_BUCKET}.files"]
            await files_coll.create_index(
                [("metadata.owner_id", 1), ("uploadDate", -1)],
                name="idx_media_owner_date",
            )
            await files_coll.create_index(
                [("metadata.owner_id", 1), ("metadata.report_id", 1)],
                name="idx_media_owner_report",
            )
            # Users collection unique index
            users_coll = self.db["users"]
            await users_coll.create_index(
                [("email", 1)],
                unique=True,
                name="idx_users_email_unique",
            )
            logger.info("MongoDB: Compound indexes verified for analysis_reports, users, and %s.files", GRIDFS_MEDIA_BUCKET)
        except Exception as exc:
            logger.warning("Failed to create MongoDB indexes: %s", exc)

    def get_reports_collection(self):
        """Return analysis_reports collection if connected, else None."""
        if not self.is_connected or self.db is None:
            return None
        return self.db["analysis_reports"]

    def get_users_collection(self):
        """Return users collection if connected, else None."""
        if not self.is_connected or self.db is None:
            return None
        return self.db["users"]

    def get_media_bucket(self) -> Optional[AsyncGridFSBucket]:
        """Return AsyncGridFSBucket if connected, else None."""
        if not self.is_connected:
            return None
        return self.media_bucket


# Global singleton database manager
db_manager = DatabaseManager()


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Recursively serialize BSON documents into JSON-compatible dictionaries:
    - ObjectId -> str
    - datetime -> ISO-8601 string in UTC
    """
    if doc is None:
        return None

    out: Dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id" and isinstance(value, ObjectId):
            out["id"] = str(value)
            out["_id"] = str(value)
        elif isinstance(value, ObjectId):
            out[key] = str(value)
        elif isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            out[key] = value.isoformat()
        elif isinstance(value, dict):
            out[key] = serialize_doc(value)
        elif isinstance(value, list):
            out[key] = [
                serialize_doc(item) if isinstance(item, dict)
                else str(item) if isinstance(item, ObjectId)
                else item.isoformat() if isinstance(item, datetime)
                else item
                for item in value
            ]
        else:
            out[key] = value
    return out
