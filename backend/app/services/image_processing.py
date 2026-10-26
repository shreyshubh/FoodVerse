"""
FoodVerse AI — Image processing service.

Responsibilities:
- Decode uploaded bytes into a valid image via OpenCV.
- Validate dimensions and pixel integrity.
- Normalize for model input (resize, channel order, tensor conversion).
"""

from __future__ import annotations

import logging
from typing import Optional

import cv2
import numpy as np

from app.core.config import (
    MAX_IMAGE_DIMENSION,
    MIN_IMAGE_DIMENSION,
    MODEL_INPUT_SIZE,
)

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Raised when an image fails validation checks."""

    def __init__(self, message: str, code: str = "INVALID_IMAGE"):
        self.message = message
        self.code = code
        super().__init__(message)


def decode_image(file_bytes: bytes) -> np.ndarray:
    """
    Decode raw file bytes into a BGR numpy array via OpenCV.

    Raises ImageValidationError if the bytes cannot be decoded.
    """
    if not file_bytes:
        raise ImageValidationError("Uploaded file is empty.", code="EMPTY_FILE")

    np_arr = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ImageValidationError(
            "File could not be decoded as a valid image. Please upload a JPEG, PNG, or WebP file.",
            code="DECODE_FAILED",
        )

    return image


def validate_image_dimensions(image: np.ndarray) -> None:
    """
    Check that the image dimensions are within configured bounds.

    Raises ImageValidationError for oversized or undersized images.
    """
    height, width = image.shape[:2]

    if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
        raise ImageValidationError(
            f"Image is too small ({width}×{height}). Minimum dimension is {MIN_IMAGE_DIMENSION}px.",
            code="IMAGE_TOO_SMALL",
        )

    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise ImageValidationError(
            f"Image is too large ({width}×{height}). Maximum dimension is {MAX_IMAGE_DIMENSION}px.",
            code="IMAGE_TOO_LARGE",
        )


def preprocess_for_model(image: np.ndarray, target_size: Optional[int] = None) -> np.ndarray:
    """
    Resize and normalize an image for model inference.

    - Converts BGR → RGB (PyTorch/torchvision convention).
    - Preserves aspect ratio by scaling the shorter dimension to 256.
    - Center crops to target_size × target_size (default 224 × 224).
    - Normalizes pixel values to [0, 1] then applies ImageNet mean/std.
    - Returns a float32 array in CHW format ready for torch.from_numpy().
    """
    if target_size is None:
        target_size = MODEL_INPUT_SIZE

    # BGR → RGB
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = rgb.shape[:2]

    # Preserve aspect ratio: scale shorter dimension to standard 256px
    resize_dim = max(int(round(target_size * 256.0 / 224.0)), target_size)
    if h < w:
        new_h = resize_dim
        new_w = int(round(w * resize_dim / h))
    else:
        new_w = resize_dim
        new_h = int(round(h * resize_dim / w))

    interpolation = cv2.INTER_AREA if (h > new_h or w > new_w) else cv2.INTER_LINEAR
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=interpolation)

    # Center crop to target_size × target_size
    top = (new_h - target_size) // 2
    left = (new_w - target_size) // 2
    cropped = resized[top:top + target_size, left:left + target_size]

    # Normalize to [0, 1]
    normalized = cropped.astype(np.float32) / 255.0

    # ImageNet mean and std (per-channel)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (normalized - mean) / std

    # HWC → CHW
    chw = np.transpose(normalized, (2, 0, 1))

    return chw
