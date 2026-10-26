"""
FoodVerse AI — Application configuration.

All environment-specific values are loaded from environment variables
with sensible defaults for local development.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

# Automatically load environment variables: prefer root Main/.env, fallback to backend/.env
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BASE_DIR / ".env")
load_dotenv()  # Fallback to current working directory if different


def _resolve_path(env_var_name: str, default: Path) -> str:
    """Resolve model or data file paths across root, backend, and absolute paths."""
    val = os.getenv(env_var_name, "").strip()
    if not val:
        return str(default)
    p = Path(val)
    if p.is_absolute() and p.exists():
        return str(p)
    if (BASE_DIR / val).exists():
        return str(BASE_DIR / val)
    if (PROJECT_ROOT / val).exists():
        return str(PROJECT_ROOT / val)
    return str(default)


# Upload constraints
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("FOODVERSE_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
}
MAX_IMAGE_DIMENSION = int(os.getenv("FOODVERSE_MAX_IMAGE_DIM", "4096"))
MIN_IMAGE_DIMENSION = int(os.getenv("FOODVERSE_MIN_IMAGE_DIM", "32"))

# Model configuration
MODEL_WEIGHTS_PATH = _resolve_path("FOODVERSE_MODEL_WEIGHTS", MODEL_DIR / "food101_mobilenetv2.pth")
CLASS_LABELS_PATH = _resolve_path("FOODVERSE_CLASS_LABELS", DATA_DIR / "food101_classes.json")
MODEL_INPUT_SIZE = int(os.getenv("FOODVERSE_MODEL_INPUT_SIZE", "224"))
CONFIDENCE_THRESHOLD = float(os.getenv("FOODVERSE_CONFIDENCE_THRESHOLD", "0.4"))
TOP_K_PREDICTIONS = int(os.getenv("FOODVERSE_TOP_K", "5"))

# Nutrition reference
NUTRITION_REFERENCE_PATH = _resolve_path("FOODVERSE_NUTRITION_REF", DATA_DIR / "nutrition_reference.json")

# Groq Cloud AI Provider Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b").strip()
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b").strip()
GROQ_TIMEOUT_SECONDS = float(os.getenv("GROQ_TIMEOUT_SECONDS", "45.0"))
GROQ_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "2"))

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "foodverse_ai").strip()
GRIDFS_MEDIA_BUCKET = os.getenv("FOODVERSE_GRIDFS_BUCKET", "foodverse_media").strip()

# Session & Security
SESSION_SECRET = os.getenv("FOODVERSE_SESSION_SECRET", "foodverse-production-session-secret-change-in-prod")
SESSION_COOKIE_NAME = "foodverse_session"
SESSION_HEADER_NAME = "X-Session-ID"

# YOLO PPE & Kitchen Detector
YOLO_PPE_MODEL_PATH = _resolve_path("FOODVERSE_YOLO_PPE_WEIGHTS", MODEL_DIR / "yolov8n_ppe.pt")
YOLO_BASE_MODEL_PATH = _resolve_path("FOODVERSE_YOLO_BASE_WEIGHTS", MODEL_DIR / "yolov8n.pt")
MAX_VIDEO_FRAMES = int(os.getenv("FOODVERSE_MAX_VIDEO_FRAMES", "10"))
VIDEO_FRAME_INTERVAL_SEC = float(os.getenv("FOODVERSE_VIDEO_FRAME_INTERVAL", "1.0"))
MAX_VIDEO_SIZE_BYTES = int(os.getenv("FOODVERSE_MAX_VIDEO_BYTES", str(25 * 1024 * 1024)))  # 25 MB

# API
API_V1_PREFIX = "/api/v1"
CORS_ORIGINS = os.getenv("FOODVERSE_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000").split(",")

# Logging
LOG_LEVEL = os.getenv("FOODVERSE_LOG_LEVEL", "INFO")
