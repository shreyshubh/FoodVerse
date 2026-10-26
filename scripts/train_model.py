"""
FoodVerse AI — Download and fine-tune MobileNetV2 on Food-101.

This script:
1. Downloads the Food-101 dataset via torchvision.
2. Fine-tunes a pretrained MobileNetV2 classifier head.
3. Saves weights to backend/models/food101_mobilenetv2.pth

Run: python scripts/train_model.py

Requirements: torch, torchvision (already in requirements.txt)
"""

import json
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
MODEL_DIR = BACKEND_DIR / "models"
DATA_DIR = BACKEND_DIR / "data"
DATASET_DIR = PROJECT_ROOT / "datasets"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Hyperparameters
BATCH_SIZE = 32
NUM_EPOCHS = 5
LEARNING_RATE = 0.001
NUM_WORKERS = 2
IMAGE_SIZE = 224


def get_transforms():
    """Data augmentation and normalization transforms."""
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    return train_transform, val_transform


def build_model(num_classes: int) -> nn.Module:
    """Build MobileNetV2 with pretrained backbone and fresh classifier."""
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    # Freeze backbone initially
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)

    return model


def train_one_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (inputs, labels) in enumerate(dataloader):
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

        if (batch_idx + 1) % 50 == 0:
            print(
                f"  Batch {batch_idx + 1}: "
                f"Loss={running_loss / (batch_idx + 1):.4f}, "
                f"Acc={100. * correct / total:.2f}%"
            )

    return running_loss / len(dataloader), 100.0 * correct / total


def validate(model, dataloader, criterion, device):
    """Validate the model."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    return running_loss / len(dataloader), 100.0 * correct / total


def main():
    print("=" * 60)
    print("FoodVerse AI — MobileNetV2 Food-101 Training")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Transforms
    train_transform, val_transform = get_transforms()

    # Download and load Food-101 dataset
    print("\nDownloading Food-101 dataset (this may take a while)...")
    train_dataset = datasets.Food101(
        root=str(DATASET_DIR),
        split="train",
        transform=train_transform,
        download=True,
    )
    val_dataset = datasets.Food101(
        root=str(DATASET_DIR),
        split="test",
        transform=val_transform,
        download=True,
    )

    # Save class names
    class_names = train_dataset.classes
    print(f"Number of classes: {len(class_names)}")

    classes_path = DATA_DIR / "food101_classes.json"
    with open(classes_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)
    print(f"Class labels saved to {classes_path}")

    # Data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=True,
    )

    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")

    # Build model
    model = build_model(num_classes=len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    # Training loop
    best_val_acc = 0.0
    print("\nStarting training...")

    for epoch in range(NUM_EPOCHS):
        print(f"\nEpoch {epoch + 1}/{NUM_EPOCHS}")
        print("-" * 40)

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step()

        print(
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%\n"
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            weights_path = MODEL_DIR / "food101_mobilenetv2.pth"
            torch.save(model.state_dict(), weights_path)
            print(f"  Best model saved to {weights_path}")

    # Unfreeze and fine-tune entire model for 2 more epochs
    print("\n\nFine-tuning entire model...")
    for param in model.parameters():
        param.requires_grad = True

    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE * 0.1)

    for epoch in range(2):
        print(f"\nFine-tune Epoch {epoch + 1}/2")
        print("-" * 40)

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        print(
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%\n"
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            weights_path = MODEL_DIR / "food101_mobilenetv2.pth"
            torch.save(model.state_dict(), weights_path)
            print(f"  Best model saved to {weights_path}")

    print(f"\n{'=' * 60}")
    print(f"Training complete. Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {MODEL_DIR / 'food101_mobilenetv2.pth'}")
    print(f"Class labels saved to: {classes_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
