"""
FoodVerse AI — Freshness & Spoilage Schemas.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class FreshnessAnalysisResponse(BaseModel):
    """Structured response for multimodal freshness analysis."""
    request_id: str
    status: Literal["success", "uncertain", "insufficient_evidence", "provider_unavailable"]
    food_name: str
    freshness_state: Literal["Fresh", "Marginal", "Spoiled", "Unverified"]
    safety_status: Literal["SAFE", "CAUTION", "UNSAFE", "UNDETERMINED"]
    confidence: float = Field(..., ge=0.0, le=100.0, description="Model confidence score 0-100")
    signs: List[str] = Field(default_factory=list, description="Observed visual degradation signs")
    reasoning: str = Field(..., description="Biochemical/visual explanation of the food condition")
    advice: str = Field(..., description="Actionable consumer guidance")
    limitations_disclaimer: str = Field(
        default="Visual inspection cannot rule out bacterial toxins or microbial contamination. Follow standard food safety regulations.",
        description="Mandatory food safety disclaimer"
    )
    provider: str = Field(default="groq-vision", description="Analysis provider name")
    report_id: Optional[str] = Field(default=None, description="Persisted analysis report ID")
    media_id: Optional[str] = Field(default=None, description="GridFS media file ID")
    media_url: Optional[str] = Field(default=None, description="Media streaming URL")
