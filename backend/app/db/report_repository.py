"""
FoodVerse AI — Analysis Reports Repository (Unified Collection).

Manages CRUD for analysis_reports collection with strict owner isolation,
BSON serialization, pagination, and dashboard summary aggregates.
Features:
  - food_recognition
  - freshness_analysis
  - hygiene_analysis
  - recipe_generation
  - meal_plan
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.db.media_repository import media_repository
from app.db.mongodb import db_manager, serialize_doc

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


class ReportRepository:
    """Repository for analysis_reports collection."""

    async def create_report(
        self,
        owner_id: str,
        feature: str,
        status: str = "completed",
        input_data: Optional[Dict[str, Any]] = None,
        result_data: Optional[Dict[str, Any]] = None,
        media_refs: Optional[List[Dict[str, Any]]] = None,
        model_info: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        error_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Persist a new analysis report.
        Returns the serialized report dictionary with 'id', or None if DB is unavailable.
        """
        coll = db_manager.get_reports_collection()
        if coll is None:
            logger.debug("Database not connected. Report persistence skipped.")
            return None

        now = datetime.now(timezone.utc)
        doc = {
            "owner_id": owner_id,
            "feature": feature,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "input": input_data or {},
            "media": media_refs or [],
            "result": result_data or {},
            "model_info": model_info or {},
            "metrics": metrics or {},
            "error_metadata": error_metadata,
        }

        try:
            insert_res = await coll.insert_one(doc)
            doc["_id"] = insert_res.inserted_id
            logger.info("Persisted report %s for feature %s (owner: %s)", str(insert_res.inserted_id), feature, owner_id)
            return serialize_doc(doc)
        except Exception as exc:
            logger.error("Failed to insert report into MongoDB: %s", exc)
            return None

    async def get_report(
        self,
        report_id_str: str,
        owner_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single report strictly scoped to the verified owner_id.
        Never returns a report belonging to another owner.
        """
        coll = db_manager.get_reports_collection()
        if coll is None:
            return None

        try:
            r_id = ObjectId(report_id_str)
        except Exception:
            return None

        try:
            doc = await coll.find_one({"_id": r_id, "owner_id": owner_id})
            if not doc:
                return None
            return serialize_doc(doc)
        except Exception as exc:
            logger.error("Error reading report %s: %s", report_id_str, exc)
            return None

    async def list_reports(
        self,
        owner_id: str,
        feature: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = DEFAULT_PAGE_SIZE,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List reports scoped to owner_id with cursor-based pagination.
        Cursor is the last seen report ObjectId string for created_at descending order.
        """
        coll = db_manager.get_reports_collection()
        if coll is None:
            return {
                "items": [],
                "next_cursor": None,
                "has_more": False,
                "total": 0,
            }

        # Clamp limit
        limit = max(1, min(limit, MAX_PAGE_SIZE))

        query: Dict[str, Any] = {"owner_id": owner_id}
        if feature:
            query["feature"] = feature
        if status:
            query["status"] = status

        if cursor:
            try:
                # In descending order by _id / created_at, next items have _id < cursor
                query["_id"] = {"$lt": ObjectId(cursor)}
            except Exception:
                pass

        try:
            cursor_res = coll.find(query).sort("_id", -1).limit(limit + 1)
            docs = await cursor_res.to_list(length=limit + 1)

            has_more = len(docs) > limit
            items_to_return = docs[:limit]
            next_cursor = str(items_to_return[-1]["_id"]) if (has_more and items_to_return) else None

            # Get total count for current query filter
            total_count = await coll.count_documents({"owner_id": owner_id, **({"feature": feature} if feature else {})})

            return {
                "items": [serialize_doc(d) for d in items_to_return],
                "next_cursor": next_cursor,
                "has_more": has_more,
                "total": total_count,
            }
        except Exception as exc:
            logger.error("Error listing reports for owner %s: %s", owner_id, exc)
            return {
                "items": [],
                "next_cursor": None,
                "has_more": False,
                "total": 0,
            }

    async def delete_report(
        self,
        report_id_str: str,
        owner_id: str,
    ) -> bool:
        """
        Delete a report and all associated media from GridFS.
        Strictly scoped to the owner_id.
        """
        coll = db_manager.get_reports_collection()
        if coll is None:
            return False

        try:
            r_id = ObjectId(report_id_str)
        except Exception:
            return False

        try:
            # 1. Fetch document to identify associated media
            doc = await coll.find_one({"_id": r_id, "owner_id": owner_id})
            if not doc:
                return False

            # 2. Cleanup associated media
            media_list = doc.get("media", [])
            for m in media_list:
                file_id = m.get("file_id")
                if file_id:
                    try:
                        await media_repository.delete_image(file_id, owner_id)
                    except Exception as m_exc:
                        logger.warning("Failed to clean up media %s: %s", file_id, m_exc)

            # 3. Delete report document
            res = await coll.delete_one({"_id": r_id, "owner_id": owner_id})
            logger.info("Deleted report %s for owner %s", report_id_str, owner_id)
            return res.deleted_count > 0
        except Exception as exc:
            logger.error("Error deleting report %s: %s", report_id_str, exc)
            return False

    async def get_dashboard_summary(self, owner_id: str) -> Dict[str, Any]:
        """
        Generate lightweight dashboard summary for owner:
        - feature counts
        - total reports
        - recent 5 reports
        """
        coll = db_manager.get_reports_collection()
        if coll is None:
            return {
                "total_reports": 0,
                "counts_by_feature": {
                    "food_recognition": 0,
                    "freshness_analysis": 0,
                    "hygiene_analysis": 0,
                    "recipe_generation": 0,
                    "meal_plan": 0,
                },
                "recent_reports": [],
            }

        try:
            # Feature counts aggregation
            pipeline = [
                {"$match": {"owner_id": owner_id}},
                {"$group": {"_id": "$feature", "count": {"$sum": 1}}},
            ]
            agg_cursor = await coll.aggregate(pipeline)
            group_results = await agg_cursor.to_list(length=100)

            counts = {
                "food_recognition": 0,
                "freshness_analysis": 0,
                "hygiene_analysis": 0,
                "recipe_generation": 0,
                "meal_plan": 0,
            }
            total = 0
            for row in group_results:
                f_name = row.get("_id")
                cnt = row.get("count", 0)
                if f_name in counts:
                    counts[f_name] = cnt
                total += cnt

            # Recent 5 reports
            recent_cursor = coll.find({"owner_id": owner_id}).sort("_id", -1).limit(5)
            recent_docs = await recent_cursor.to_list(length=5)

            # Format concise summaries for recent items
            recent_summaries = []
            for d in recent_docs:
                s_doc = serialize_doc(d)
                feature = s_doc.get("feature")
                result = s_doc.get("result", {})
                media = s_doc.get("media", [])

                title = "Analysis Report"
                subtitle = ""
                badge = feature

                if feature == "food_recognition":
                    title = result.get("predicted_food", "Food Recognition")
                    conf = result.get("confidence", 0)
                    subtitle = f"{conf:.1f}% confidence"
                elif feature == "freshness_analysis":
                    title = result.get("food_name", "Freshness Inspection")
                    state = result.get("freshness_state", "Evaluated")
                    subtitle = f"{state} • {result.get('safety_status', '')}"
                elif feature == "hygiene_analysis":
                    title = "Kitchen Hygiene Audit"
                    subtitle = f"Compliance: {result.get('compliance_status', 'N/A')}"
                elif feature == "recipe_generation":
                    title = result.get("title", "Smart Recipe")
                    subtitle = f"{result.get('prep_time_minutes', 0) + result.get('cook_time_minutes', 0)} mins • {result.get('difficulty', '')}"
                elif feature == "meal_plan":
                    title = "Personalized Meal Plan"
                    cals = result.get("today_plan", {}).get("calories_total", 0)
                    subtitle = f"{cals:.0f} kcal target"

                recent_summaries.append({
                    "id": s_doc.get("id"),
                    "feature": feature,
                    "title": title,
                    "subtitle": subtitle,
                    "badge": badge,
                    "status": s_doc.get("status"),
                    "created_at": s_doc.get("created_at"),
                    "thumbnail_url": f"/api/v1/media/{media[0]['file_id']}" if media else None,
                })

            return {
                "total_reports": total,
                "counts_by_feature": counts,
                "recent_reports": recent_summaries,
            }
        except Exception as exc:
            logger.error("Error generating dashboard summary for owner %s: %s", owner_id, exc)
            return {
                "total_reports": 0,
                "counts_by_feature": {
                    "food_recognition": 0,
                    "freshness_analysis": 0,
                    "hygiene_analysis": 0,
                    "recipe_generation": 0,
                    "meal_plan": 0,
                },
                "recent_reports": [],
            }


report_repository = ReportRepository()
