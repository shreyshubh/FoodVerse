"""
FoodVerse AI — Analysis Reports History API Routes.

Owner-scoped endpoints for listing, inspecting, and deleting historical reports.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.session import get_current_owner_id
from app.db.report_repository import report_repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history/summary", summary="Get dashboard summary counts and recent reports")
async def get_dashboard_summary(
    owner_id: str = Depends(get_current_owner_id),
) -> Dict[str, Any]:
    """
    Returns total reports, feature counts, and concise recent activity
    strictly scoped to the current verified session owner.
    """
    summary = await report_repository.get_dashboard_summary(owner_id)
    return {
        "status": "success",
        "data": summary,
    }


@router.get("/history", summary="List paginated analysis reports")
async def list_history(
    feature: Optional[str] = Query(None, description="Filter by feature type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by report status"),
    limit: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    cursor: Optional[str] = Query(None, description="Pagination cursor (report ID)"),
    owner_id: str = Depends(get_current_owner_id),
) -> Dict[str, Any]:
    """
    Paginated list of the current owner's historical reports.
    Supports feature filtering and cursor-based pagination.
    """
    res = await report_repository.list_reports(
        owner_id=owner_id,
        feature=feature,
        status=status_filter,
        limit=limit,
        cursor=cursor,
    )
    return {
        "status": "success",
        **res,
    }


@router.get("/history/{report_id}", summary="Get full analysis report by ID")
async def get_history_report(
    report_id: str,
    owner_id: str = Depends(get_current_owner_id),
) -> Dict[str, Any]:
    """
    Returns full analysis report if and only if it belongs to current session owner.
    Returns 404 if not found or unauthorized to prevent ID enumeration.
    """
    report = await report_repository.get_report(report_id, owner_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Report not found or access denied."},
        )
    return {
        "status": "success",
        "report": report,
    }


@router.delete("/history/{report_id}", summary="Delete an analysis report and associated media")
async def delete_history_report(
    report_id: str,
    owner_id: str = Depends(get_current_owner_id),
) -> Dict[str, Any]:
    """
    Deletes the selected report and its associated GridFS media.
    Strictly scoped to current owner.
    """
    deleted = await report_repository.delete_report(report_id, owner_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Report not found or access denied."},
        )
    return {
        "status": "success",
        "message": f"Report {report_id} and associated media successfully removed.",
    }
