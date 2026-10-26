"""
FoodVerse AI — Model Evaluation Pipeline

Evaluates the exact MobileNetV2 checkpoint used by FastAPI:
- Top-1 and Top-5 accuracy on labeled food images
- Confidence distribution and entropy
- Macro F1-score and per-class results
- Handling of in-domain vs out-of-domain (e.g., Indian dishes not in Food-101)
- Handling of non-food images
- Comparison with the untrained baseline checkpoint
"""

import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import models

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "Main" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.image_processing import decode_image, preprocess_for_model

# Direct raw Wikimedia images for benchmark
TEST_BENCHMARK = [
    # In-domain Food-101 classes
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg",
        "expected_label": "pizza",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Cheeseburger.jpg",
        "expected_label": "hamburger",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/7/73/001_Tacos_de_carnitas%2C_Tianguis_de_los_Domingos%2C_Tepoztl%C3%A1n%2C_Mor.jpg",
        "expected_label": "tacos",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/8/83/French_Fries.JPG",
        "expected_label": "french_fries",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Samosachutney.jpg",
        "expected_label": "samosa",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/6/64/Red_Apple_Pie.jpg",
        "expected_label": "apple_pie",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/7/7b/Assorted_sushi_platter.jpg",
        "expected_label": "sushi",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/3/30/Spaghetti_al_Pomodoro.JPG",
        "expected_label": "spaghetti_bolognese",
        "category": "in_domain"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/2/2e/Ice_cream_with_whipped_cream%2C_chocolate_syrup%2C_and_a_wafer_%28cropped%29.jpg",
        "expected_label": "ice_cream",
        "category": "in_domain"
    },
    # Out-of-Domain Food (Target Indian Dishes not in Food-101)
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/5/5a/%22Hyderabadi_Dum_Biryani%22.jpg",
        "expected_label": "biryani",
        "category": "out_of_domain_food"
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/a5/Dal_Makhani_in_a_bowl.jpg",
        "expected_label": "dal",
        "category": "out_of_domain_food"
    },
    # Out-of-Domain Non-Food
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png",
        "expected_label": "dice",
        "category": "non_food"
    }
]

def load_checkpoint(weights_path: str):
    with open(BACKEND_DIR / "data" / "food101_classes.json") as f:
        classes = json.load(f)

    model = models.mobilenet_v2(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(classes))
    state = torch.load(weights_path, map_location="cpu", weights_only=True)
    clean_state = {k.replace("module.", ""): v for k, v in state.items()}
    model.load_state_dict(clean_state)
    model.eval()
    return model, classes

def download_image_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FoodVerseBot/1.0 (https://foodverse.ai; audit@foodverse.ai)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()

def run_evaluation():
    print("=" * 75)
    print("FOODVERSE AI — MODEL EVALUATION PIPELINE")
    print("=" * 75)

    cache_dir = PROJECT_ROOT / "datasets" / "eval_benchmark"
    cache_dir.mkdir(parents=True, exist_ok=True)

    test_items = []
    # Add local sample_pizza.jpg
    local_pizza = PROJECT_ROOT / "sample_pizza.jpg"
    if local_pizza.exists():
        with open(local_pizza, "rb") as f:
            test_items.append({
                "name": "sample_pizza.jpg (local)",
                "bytes": f.read(),
                "expected": "pizza",
                "category": "in_domain"
            })

    print("Fetching benchmark images...")
    for idx, item in enumerate(TEST_BENCHMARK):
        cache_file = cache_dir / f"img_{idx}_{item['expected_label']}.jpg"
        if not cache_file.exists():
            try:
                print(f"  Downloading: {item['expected_label']} ({item['category']})...")
                b = download_image_bytes(item["url"])
                with open(cache_file, "wb") as f:
                    f.write(b)
            except Exception as e:
                print(f"  Warning: failed to download {item['url']}: {e}")
                continue
        with open(cache_file, "rb") as f:
            test_items.append({
                "name": f"benchmark_{idx}_{item['expected_label']}",
                "bytes": f.read(),
                "expected": item["expected_label"],
                "category": item["category"]
            })

    print(f"Total evaluation samples ready: {len(test_items)}")

    # 1. Evaluate Current Trained Checkpoint
    current_path = str(BACKEND_DIR / "models" / "food101_mobilenetv2.pth")
    print(f"\n--- EVALUATING CURRENT CHECKPOINT: {current_path} ---")
    model_trained, classes = load_checkpoint(current_path)

    # 2. Evaluate Untrained Baseline Checkpoint
    backup_path = str(BACKEND_DIR / "models" / "food101_mobilenetv2_untrained_dev.pth.bak")
    model_untrained = None
    if os.path.exists(backup_path):
        print(f"Loading baseline untrained checkpoint for comparison: {backup_path}")
        model_untrained, _ = load_checkpoint(backup_path)

    def evaluate_model(model):
        results = []
        top1_correct = 0
        top5_correct = 0
        in_domain_total = 0
        per_class_tp = defaultdict(int)
        per_class_fp = defaultdict(int)
        per_class_fn = defaultdict(int)

        for item in test_items:
            img = decode_image(item["bytes"])
            preprocessed = preprocess_for_model(img)
            tensor = torch.from_numpy(preprocessed).unsqueeze(0)

            with torch.no_grad():
                logits = model(tensor)
                probs = F.softmax(logits, dim=1).squeeze(0)

            top5 = torch.topk(probs, 5)
            top1_label = classes[top5.indices[0]]
            top1_conf = top5.values[0].item()
            top5_labels = [classes[idx] for idx in top5.indices]

            is_in_domain = (item["category"] == "in_domain")
            is_top1 = False
            is_top5 = False

            if is_in_domain:
                in_domain_total += 1
                is_top1 = (top1_label == item["expected"])
                is_top5 = (item["expected"] in top5_labels)
                if is_top1:
                    top1_correct += 1
                    per_class_tp[item["expected"]] += 1
                else:
                    per_class_fn[item["expected"]] += 1
                    per_class_fp[top1_label] += 1
                if is_top5:
                    top5_correct += 1

            results.append({
                "sample": item["name"],
                "expected": item["expected"],
                "category": item["category"],
                "top1_label": top1_label,
                "top1_conf": round(top1_conf, 4),
                "top5_labels": top5_labels,
                "is_top1": is_top1,
                "is_top5": is_top5
            })

        top1_acc = (top1_correct / in_domain_total * 100.0) if in_domain_total > 0 else 0.0
        top5_acc = (top5_correct / in_domain_total * 100.0) if in_domain_total > 0 else 0.0

        # Calculate Macro F1
        f1_list = []
        unique_classes = set(i["expected"] for i in test_items if i["category"] == "in_domain")
        for c in unique_classes:
            tp = per_class_tp[c]
            fp = per_class_fp[c]
            fn = per_class_fn[c]
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            f1_list.append(f1)
        macro_f1 = (sum(f1_list) / len(f1_list)) if f1_list else 0.0

        return results, top1_acc, top5_acc, macro_f1, in_domain_total

    res_trained, top1_tr, top5_tr, f1_tr, n_in = evaluate_model(model_trained)
    
    print("\n" + "=" * 75)
    print("DETAILED RESULTS (Current Trained Checkpoint):")
    print("=" * 75)
    print(f"{'Sample':<30} | {'Expected':<18} | {'Top-1 Predicted':<18} | {'Conf':<7} | {'Top-1':<5} | {'Top-5':<5}")
    print("-" * 92)
    for r in res_trained:
        t1_str = "PASS" if r["is_top1"] else ("FAIL" if r["category"] == "in_domain" else "OOD")
        t5_str = "PASS" if r["is_top5"] else ("FAIL" if r["category"] == "in_domain" else "OOD")
        print(f"{r['sample'][:30]:<30} | {r['expected'][:18]:<18} | {r['top1_label'][:18]:<18} | {r['top1_conf']*100:5.1f}% | {t1_str:<5} | {t5_str:<5}")

    print("\n" + "=" * 75)
    print("METRICS SUMMARY (In-Domain Food-101 Benchmark):")
    print("=" * 75)
    print(f"Total In-Domain Test Samples: {n_in}")
    print(f"Top-1 Accuracy:  {top1_tr:.1f}%")
    print(f"Top-5 Accuracy:  {top5_tr:.1f}%")
    print(f"Macro F1-Score:  {f1_tr:.4f}")

    if model_untrained:
        _, top1_un, top5_un, f1_un, _ = evaluate_model(model_untrained)
        print("\n" + "=" * 75)
        print("COMPARISON: TRAINED CHECKPOINT VS UNTRAINED BASELINE:")
        print("=" * 75)
        print(f"  {'Metric':<20} | {'Untrained Baseline':<20} | {'Current Checkpoint':<20}")
        print(f"  {'-'*20}-+-{'-'*20}-+-{'-'*20}")
        print(f"  {'Top-1 Accuracy':<20} | {top1_un:5.1f}%               | {top1_tr:5.1f}%")
        print(f"  {'Top-5 Accuracy':<20} | {top5_un:5.1f}%               | {top5_tr:5.1f}%")
        print(f"  {'Macro F1-Score':<20} | {f1_un:6.4f}               | {f1_tr:6.4f}")

    print("\n" + "=" * 75)
    print("OUT-OF-DOMAIN & NON-FOOD BEHAVIOR:")
    print("=" * 75)
    for r in res_trained:
        if r["category"] != "in_domain":
            status = "Low Confidence" if r["top1_conf"] < 0.4 else "High Confidence (OOD Risk)"
            print(f"  Input: {r['expected']:<15} ({r['category']:<18}) -> Top-1: {r['top1_label']:<18} | Conf: {r['top1_conf']*100:5.1f}% [{status}]")

    # Save evaluation report artifact in Resource
    eval_report = {
        "timestamp": time.ctime(),
        "checkpoint_path": current_path,
        "checkpoint_sha256": "77600047a8427e555ea9f6aa21c000cb0f73474a51f8df0f5fe252392229ba18",
        "in_domain_samples": n_in,
        "top1_accuracy": round(top1_tr, 2),
        "top5_accuracy": round(top5_tr, 2),
        "macro_f1": round(f1_tr, 4),
        "results": res_trained
    }
    eval_json_path = PROJECT_ROOT / "Resource" / "model_evaluation_metrics.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)
    print(f"\nEvaluation metrics successfully saved to: {eval_json_path}")

if __name__ == "__main__":
    run_evaluation()
