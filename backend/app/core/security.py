"""
FoodVerse AI — Authentication Security & Cryptographic Tokens.

Provides PBKDF2-HMAC-SHA256 password hashing with random salt and
HMAC-SHA256 signed access tokens with expiration.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from typing import Optional

from app.core.config import SESSION_SECRET

logger = logging.getLogger(__name__)

ITERATIONS = 100_000
TOKEN_VALIDITY_SECONDS = 60 * 60 * 24 * 30  # 30 days


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256 and unique 16-byte random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
    )
    return f"pbkdf2_sha256${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against PBKDF2 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3 or parts[0] != "pbkdf2_sha256":
            return False
        _, salt, expected_hex = parts
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            ITERATIONS,
        )
        return hmac.compare_digest(computed_key.hex(), expected_hex)
    except Exception as exc:
        logger.error("Error verifying password: %s", exc)
        return False


def create_access_token(user_id: str) -> str:
    """
    Generate an HMAC-signed access token for a user.
    Format: auth.<user_id>.<expires_timestamp>.<signature>
    """
    expires = int(time.time()) + TOKEN_VALIDITY_SECONDS
    payload = f"auth.{user_id}.{expires}"
    sig = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{sig}"


def verify_access_token(token: Optional[str]) -> Optional[str]:
    """
    Validate an access token and return user_id if valid and unexpired.
    Returns None if signature is invalid or token has expired.
    """
    if not token or not isinstance(token, str):
        return None

    # Handle optional 'Bearer ' prefix
    cleaned = token.strip()
    if cleaned.lower().startswith("bearer "):
        cleaned = cleaned[7:].strip()

    parts = cleaned.split(".")
    if len(parts) != 4 or parts[0] != "auth":
        return None

    _, user_id, expires_str, provided_sig = parts

    try:
        expires = int(expires_str)
        if time.time() > expires:
            return None  # Expired
    except ValueError:
        return None

    payload = f"auth.{user_id}.{expires_str}"
    expected_sig = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if hmac.compare_digest(provided_sig, expected_sig):
        return user_id

    return None
