"""
FoodVerse AI — Freshness & Spoilage Service.

Combines Groq multimodal vision analysis (qwen/qwen3.8-27b) with a deterministic food safety policy layer.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from app.core.groq_provider import groq_provider
from app.schemas.freshness import FreshnessAnalysisResponse

logger = logging.getLogger(__name__)

# Shelf-life rule table for deterministic food safety check (USDA / FDA guidance)
HIGH_RISK_SHELF_LIFE_DAYS = {
    "Room Temp": 2,  # Most perishable food unsafe after 2 days at room temperature
    "Refrigerator": 7,  # Cooked leftovers / cut fruit typically safe for 3-5 days, max 7
    "Pantry": 14,
    "Countertop": 3,
}


class FreshnessService:
    """Orchestrates visual freshness analysis and deterministic food safety policy."""

    def analyze(
        self,
        image_bytes: bytes,
        food_name: Optional[str] = None,
        storage_type: Optional[str] = "Room Temp",
        storage_days: Optional[int] = 1,
        sensory_notes: Optional[str] = None,
    ) -> FreshnessAnalysisResponse:
        """Analyze image and context, returning a validated FreshnessAnalysisResponse."""
        request_id = str(uuid.uuid4())

        # 1. Check Groq Provider
        if not groq_provider.is_available:
            return FreshnessAnalysisResponse(
                request_id=request_id,
                status="provider_unavailable",
                food_name=food_name or "Food Item",
                freshness_state="Unverified",
                safety_status="UNDETERMINED",
                confidence=0.0,
                signs=["AI provider key not configured"],
                reasoning="Live multimodal visual analysis requires GROQ_API_KEY. Set the key in backend .env to enable neural spoilage detection via qwen/qwen3.8-27b.",
                advice="Inspect the food manually for foul odor, slimy texture, or visible mold bloom before consuming.",
                provider="offline-policy",
            )

        # 2. Invoke Groq Multimodal Vision (qwen/qwen3.8-27b)
        groq_result = groq_provider.analyze_freshness(
            image_bytes=image_bytes,
            food_name=food_name,
            storage_type=storage_type,
            storage_days=storage_days,
        )

        if groq_result.get("status") in {"error", "provider_unavailable"}:
            return FreshnessAnalysisResponse(
                request_id=request_id,
                status="provider_unavailable" if groq_result.get("status") == "provider_unavailable" else "uncertain",
                food_name=food_name or "Food Item",
                freshness_state="Unverified",
                safety_status="UNDETERMINED",
                confidence=0.0,
                signs=["Analysis service error"],
                reasoning=groq_result.get("error", "Failed to connect to vision provider."),
                advice="Do not consume food showing questionable signs.",
                provider=f"groq-{groq_provider.vision_model}",
            )

        # 3. Parse Model Output
        detected_food = groq_result.get("detected_food") or food_name or "Food Item"
        freshness_state = groq_result.get("freshness_state", "Marginal")
        safety_status = groq_result.get("safety_status", "CAUTION")
        confidence = float(groq_result.get("confidence", 70.0))
        observed_signs = groq_result.get("observed_signs", [])
        reasoning = groq_result.get("reasoning", "Visual inspection completed.")
        advice = groq_result.get("advice", "Consume within recommended storage window.")

        # 4. Deterministic Food Safety Override Layer
        max_safe_days = HIGH_RISK_SHELF_LIFE_DAYS.get(storage_type, 3)
        if storage_days and storage_days > max_safe_days:
            if safety_status == "SAFE":
                safety_status = "CAUTION"
                observed_signs.append(f"Exceeded typical {storage_type} storage threshold ({storage_days} days > {max_safe_days} days max)")
                advice = f"Warning: Stored for {storage_days} days under {storage_type}. Inspect carefully for odor or sliminess before eating."

        return FreshnessAnalysisResponse(
            request_id=request_id,
            status="success",
            food_name=detected_food,
            freshness_state=freshness_state if freshness_state in {"Fresh", "Marginal", "Spoiled", "Unverified"} else "Marginal",
            safety_status=safety_status if safety_status in {"SAFE", "CAUTION", "UNSAFE", "UNDETERMINED"} else "CAUTION",
            confidence=max(0.0, min(100.0, confidence)),
            signs=observed_signs,
            reasoning=reasoning,
            advice=advice,
            limitations_disclaimer="Visual inspection cannot prove microbiological safety. Bacterial toxins, viral contamination, or internal pathogens may be present without observable outward signs.",
            provider=f"groq-{groq_provider.vision_model}",
        )


freshness_service = FreshnessService()
