"""
FoodVerse AI — Food recognition service.

Responsibilities:
- Load a MobileNetV2 model fine-tuned on Food-101 through a replaceable adapter.
- Run inference on preprocessed images.
- Normalize output to {label, confidence, top-k alternatives}.
- Handle missing weights, initialization failures, and low-confidence predictions.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models

from app.core.config import (
    CLASS_LABELS_PATH,
    CONFIDENCE_THRESHOLD,
    MODEL_WEIGHTS_PATH,
    TOP_K_PREDICTIONS,
)

logger = logging.getLogger(__name__)


class ModelUnavailableError(Exception):
    """Raised when the model cannot be loaded or is not ready."""

    def __init__(self, message: str = "Food recognition model is not available."):
        self.message = message
        super().__init__(message)


class FoodRecognitionResult:
    """Structured result from model inference."""

    __slots__ = ("label", "confidence", "canonical_food_id", "alternatives", "needs_confirmation")

    def __init__(
        self,
        label: str,
        confidence: float,
        canonical_food_id: Optional[str],
        alternatives: list[dict],
        needs_confirmation: bool,
    ):
        self.label = label
        self.confidence = confidence
        self.canonical_food_id = canonical_food_id
        self.alternatives = alternatives
        self.needs_confirmation = needs_confirmation


class FoodRecognitionService:
    """
    Adapter for food recognition model.

    Designed to be replaceable: swap the model architecture and weights
    without changing the service interface.
    """

    def __init__(self) -> None:
        self._model: Optional[torch.nn.Module] = None
        self._class_labels: Optional[list[str]] = None
        self._device = torch.device("cpu")
        self._ready = False
        self._init_error: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        """
        Load model weights and class labels.

        Call once at startup. If weights or labels are missing, the service
        remains in an unavailable state with a descriptive error.
        """
        try:
            self._load_class_labels()
            self._load_model()
            self._ready = True
            logger.info(
                "Food recognition model loaded successfully. Classes: %d",
                len(self._class_labels) if self._class_labels else 0,
            )
        except Exception as exc:
            self._ready = False
            self._init_error = str(exc)
            logger.warning("Food recognition model initialization failed: %s", exc)

    def _load_class_labels(self) -> None:
        """Load the class label mapping from JSON."""
        labels_path = Path(CLASS_LABELS_PATH)
        if not labels_path.exists():
            raise FileNotFoundError(
                f"Class labels file not found at {labels_path}. "
                "Please provide a food101_classes.json file."
            )

        with open(labels_path, "r", encoding="utf-8") as f:
            self._class_labels = json.load(f)

        if not isinstance(self._class_labels, list) or len(self._class_labels) == 0:
            raise ValueError("Class labels file must contain a non-empty JSON array of strings.")

    def _load_model(self) -> None:
        """Load the MobileNetV2 model with custom classifier head."""
        weights_path = Path(MODEL_WEIGHTS_PATH)
        num_classes = len(self._class_labels)

        if not weights_path.exists():
            raise FileNotFoundError(
                f"Model weights file not found at {weights_path}. "
                "Please provide the trained model weights."
            )

        # Build MobileNetV2 architecture with matching classifier
        model = models.mobilenet_v2(weights=None)
        model.classifier[1] = torch.nn.Linear(
            model.classifier[1].in_features, num_classes
        )

        # Load trained weights
        state_dict = torch.load(
            weights_path, map_location=self._device, weights_only=True
        )
        model.load_state_dict(state_dict)
        model.to(self._device)
        model.eval()

        self._model = model

    def predict(self, preprocessed_image: np.ndarray) -> FoodRecognitionResult:
        """
        Run inference on a preprocessed image (CHW float32 numpy array).

        Returns a FoodRecognitionResult with label, confidence, and alternatives.
        Raises ModelUnavailableError if the model is not loaded.
        """
        if not self._ready or self._model is None or self._class_labels is None:
            raise ModelUnavailableError(
                self._init_error or "Food recognition model is not available."
            )

        try:
            # Convert to tensor: add batch dimension
            tensor = torch.from_numpy(preprocessed_image).unsqueeze(0).to(self._device)

            with torch.no_grad():
                logits = self._model(tensor)
                probabilities = F.softmax(logits, dim=1)

            probs_np = probabilities.squeeze(0).cpu().numpy()

            # Top-k predictions
            top_k = min(TOP_K_PREDICTIONS, len(self._class_labels))
            top_indices = np.argsort(probs_np)[::-1][:top_k]

            top_label = self._class_labels[top_indices[0]]
            top_confidence = float(probs_np[top_indices[0]])

            # Canonical ID is the label in snake_case (matches nutrition reference keys)
            canonical_id = top_label.lower().replace(" ", "_")

            alternatives = []
            for idx in top_indices[1:]:
                alt_label = self._class_labels[idx]
                alternatives.append({
                    "label": alt_label,
                    "confidence": round(float(probs_np[idx]), 4),
                })

            needs_confirmation = top_confidence < CONFIDENCE_THRESHOLD

            return FoodRecognitionResult(
                label=top_label,
                confidence=round(top_confidence, 4),
                canonical_food_id=canonical_id,
                alternatives=alternatives,
                needs_confirmation=needs_confirmation,
            )

        except ModelUnavailableError:
            raise
        except Exception as exc:
            logger.error("Model inference failed: %s", exc, exc_info=True)
            raise ModelUnavailableError(
                "An error occurred during food recognition. Please try again."
            ) from exc


# Module-level singleton — initialized by app startup
food_recognition_service = FoodRecognitionService()
