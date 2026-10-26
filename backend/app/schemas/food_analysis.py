"""
FoodVerse AI — Pydantic response/error schemas for the food analysis endpoint.

These schemas define the API contract between frontend and backend.
Null means unavailable, never zero.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FoodPrediction(BaseModel):
    """A single food prediction from the recognition model."""

    label: str = Field(..., description="Predicted food label")
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Model confidence in [0, 1]; null if uncalibrated",
    )
    canonical_food_id: Optional[str] = Field(
        None,
        description="Canonical key for nutrition lookup; null if unmapped",
    )


class NutritionEstimate(BaseModel):
    """Estimated macronutrient values for the recognized food."""

    basis: str = Field(
        ...,
        description="One of: per_100_g, user_portion, unavailable",
    )
    serving_grams: Optional[float] = Field(
        None,
        ge=0.0,
        description="Serving size in grams; null when portion is unknown",
    )
    calories_kcal: Optional[float] = Field(
        None,
        ge=0.0,
        description="Energy in kcal; null means unavailable, not zero",
    )
    protein_g: Optional[float] = Field(
        None,
        ge=0.0,
        description="Protein in grams; null means unavailable",
    )
    carbohydrates_g: Optional[float] = Field(
        None,
        ge=0.0,
        description="Carbohydrates in grams; null means unavailable",
    )
    fat_g: Optional[float] = Field(
        None,
        ge=0.0,
        description="Fat in grams; null means unavailable",
    )
    source: Optional[str] = Field(
        None,
        description="Reference data source identifier",
    )


class HealthScore(BaseModel):
    """
    Placeholder health score.

    Formula/scale not yet approved — value is always null in v1.
    """

    value: Optional[float] = Field(
        None,
        description="Score value; null until formula is approved",
    )
    scale: Optional[str] = Field(
        None,
        description="Score scale description; null until approved",
    )
    rationale: list[str] = Field(
        default_factory=list,
        description="Explanation items for the score",
    )
    method_version: Optional[str] = Field(
        None,
        description="Version of the scoring methodology; null until approved",
    )


class FoodAnalysisResponse(BaseModel):
    """Top-level successful response for food analysis."""

    request_id: str = Field(..., description="Unique request identifier")
    status: str = Field(
        ...,
        description="One of: success, needs_confirmation, inconclusive",
    )
    prediction: Optional[FoodPrediction] = Field(
        None,
        description="Model prediction; null when model is unavailable",
    )
    nutrition: NutritionEstimate
    health_score: HealthScore
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made during analysis",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings about the analysis quality or limitations",
    )
    report_id: Optional[str] = Field(
        default=None,
        description="Persisted analysis report ID in MongoDB analysis_reports",
    )
    media_id: Optional[str] = Field(
        default=None,
        description="GridFS media file ID for the uploaded food image",
    )
    media_url: Optional[str] = Field(
        default=None,
        description="Streaming endpoint URL for the uploaded food image",
    )


class ApiErrorDetail(BaseModel):
    """Structured error detail — no tracebacks or filesystem paths."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Safe, user-facing error message")
    request_id: Optional[str] = Field(None, description="Request ID for diagnostics")


class ApiErrorResponse(BaseModel):
    """Top-level error response envelope."""

    error: ApiErrorDetail
