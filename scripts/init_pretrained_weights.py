"""
FoodVerse AI — Initialize MobileNetV2 weights for development testing.

Creates an initialized weights checkpoint at:
  backend/models/food101_mobilenetv2.pth

This checkpoint transfers feature extraction weights from torchvision's
pretrained MobileNetV2 into the Food-101 architecture (101 output classes),
allowing immediate local end-to-end testing of the vision pipeline.

To train/fine-tune to full Food-101 accuracy:
  python scripts/train_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MODEL_DIR = BACKEND_DIR / "models"
DATA_DIR = BACKEND_DIR / "data"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def init_weights():
    labels_path = DATA_DIR / "food101_classes.json"
    if not labels_path.exists():
        print(f"Error: {labels_path} not found.")
        return

    with open(labels_path, "r", encoding="utf-8") as f:
        classes = json.load(f)

    num_classes = len(classes)
    print(f"Loaded {num_classes} classes from {labels_path.name}")

    # Load MobileNetV2 with default pretrained backbone
    print("Loading pretrained MobileNetV2 backbone...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)

    # Replace classifier head for 101 classes
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    # Save state dict
    dest = MODEL_DIR / "food101_mobilenetv2.pth"
    torch.save(model.state_dict(), dest)
    print(f"Successfully saved checkpoint to: {dest}")
    print(f"File size: {dest.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    init_weights()
