"""
FoodVerse AI — Hygiene & Safety Monitor Schemas.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class HygieneViolationItem(BaseModel):
    """Specific violation detected by YOLO PPE detector."""
    violation_id: str
    violation_type: Literal[
        "no_gloves", "no_hairnet", "no_mask", "unauthorized_item", "improper_ppe"
    ]
    label: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    bounding_box: Optional[List[float]] = Field(
        default=None, description="[x1, y1, x2, y2] normalized to image dimensions"
    )
    frame_timestamp_sec: float = 0.0
    description: str


class HygieneInspectionResponse(BaseModel):
    """Structured response for kitchen hygiene and PPE inspection."""
    request_id: str
    status: Literal["success", "no_person_detected", "not_assessable", "model_unavailable", "low_confidence"]
    overall_score: Optional[int] = Field(default=None, ge=0, le=100, description="Compliance score out of 100, or None if indeterminate/not assessable")
    risk_level: Literal["LOW RISK", "MODERATE RISK", "HIGH RISK", "CRITICAL RISK", "NOT ASSESSABLE", "INDETERMINATE"]
    frames_analyzed: int
    persons_observed: int
    alerts: List[HygieneViolationItem] = Field(default_factory=list)
    compliance_breakdown: Dict[str, Optional[int]] = Field(
        default_factory=dict, description="Per-category compliance score (e.g. gloves, hairnets, masks), or None if indeterminate"
    )
    ai_summary: str
    audit_report_text: str
    detector_provenance: str = Field(
        default="YOLOv8n-PPE (keremberke/yolov8n-protective-equipment-detection)",
        description="Object detector model provenance"
    )
    report_id: Optional[str] = Field(default=None, description="Persisted analysis report ID")
    evidence_media_ids: List[str] = Field(default_factory=list, description="GridFS media file IDs for keyframe evidence")
