"""
FoodVerse AI — User Accounts & Profile Repository.

Manages MongoDB persistence for user accounts in the 'users' collection,
including profile data (name, email, birthday), credentials, and report ownership linking.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from bson import ObjectId

from app.db.mongodb import db_manager, serialize_doc

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for users collection."""

    async def create_user(
        self,
        name: str,
        email: str,
        birthday: str,
        password_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new registered user in MongoDB.
        Returns serialized user document without password_hash, or None if failed.
        """
        coll = db_manager.get_users_collection()
        if coll is None:
            logger.error("Database unavailable. Cannot create user.")
            return None

        clean_email = email.strip().lower()
        now = datetime.now(timezone.utc)
        doc = {
            "name": name.strip(),
            "email": clean_email,
            "birthday": birthday.strip(),
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }

        try:
            result = await coll.insert_one(doc)
            doc["_id"] = result.inserted_id
            logger.info("Created user account for %s (id: %s)", clean_email, result.inserted_id)
            serialized = serialize_doc(doc)
            if serialized:
                serialized.pop("password_hash", None)
            return serialized
        except Exception as exc:
            logger.error("Failed to create user %s: %s", clean_email, exc)
            raise exc

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by lowercased email, returns raw document including password_hash for verification."""
        coll = db_manager.get_users_collection()
        if coll is None:
            return None

        clean_email = email.strip().lower()
        try:
            doc = await coll.find_one({"email": clean_email})
            return serialize_doc(doc)
        except Exception as exc:
            logger.error("Error finding user by email %s: %s", clean_email, exc)
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find a user by ID, returns sanitized profile without password_hash."""
        coll = db_manager.get_users_collection()
        if coll is None:
            return None

        try:
            oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            doc = await coll.find_one({"_id": oid})
            serialized = serialize_doc(doc)
            if serialized:
                serialized.pop("password_hash", None)
            return serialized
        except Exception as exc:
            logger.error("Error finding user by id %s: %s", user_id, exc)
            return None

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch summary statistics for a user's activity:
        Total reports saved, breakdown by feature, and recent items count.
        """
        reports_coll = db_manager.get_reports_collection()
        if reports_coll is None:
            return {"total_reports": 0, "counts_by_feature": {}}

        try:
            pipeline = [
                {"$match": {"owner_id": str(user_id)}},
                {"$group": {"_id": "$feature", "count": {"$sum": 1}}},
            ]
            feature_counts: Dict[str, int] = {}
            total = 0
            cursor = await reports_coll.aggregate(pipeline)
            for item in await cursor.to_list(length=100):
                feat = item.get("_id", "unknown")
                cnt = item.get("count", 0)
                feature_counts[feat] = cnt
                total += cnt

            return {
                "total_reports": total,
                "counts_by_feature": feature_counts,
            }
        except Exception as exc:
            logger.error("Error fetching stats for user %s: %s", user_id, exc)
            return {"total_reports": 0, "counts_by_feature": {}}

    async def claim_session_reports(self, anonymous_owner_id: str, authenticated_user_id: str) -> int:
        """
        Transfer reports created under an anonymous session to the authenticated user's account.
        Returns the number of claimed reports.
        """
        if not anonymous_owner_id or not authenticated_user_id or anonymous_owner_id == authenticated_user_id:
            return 0

        reports_coll = db_manager.get_reports_collection()
        if reports_coll is None:
            return 0

        try:
            result = await reports_coll.update_many(
                {"owner_id": anonymous_owner_id},
                {"$set": {"owner_id": authenticated_user_id, "updated_at": datetime.now(timezone.utc)}},
            )
            claimed = result.modified_count
            if claimed > 0:
                logger.info("Claimed %d reports from anonymous session %s to user %s", claimed, anonymous_owner_id, authenticated_user_id)
            return claimed
        except Exception as exc:
            logger.warning("Failed to claim session reports: %s", exc)
            return 0


# Global singleton instance
user_repository = UserRepository()
