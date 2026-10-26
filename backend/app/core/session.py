"""
FoodVerse AI — Anonymous Session Management & Owner Scoping.

Provides cryptographically signed, backend-issued anonymous session identifiers
suitable for Vercel (frontend) + Render (backend) deployment.
Session tokens: <uuid>.<hmac_sha256>

Anonymous browser/session history is scoped to the issuing browser/device
and is not equivalent to cross-device authenticated user accounts.
"""
from __future__ import annotations

import hmac
import hashlib
import logging
import uuid
from typing import Optional, Tuple

from fastapi import Request, Response

from app.core.config import (
    SESSION_COOKIE_NAME,
    SESSION_HEADER_NAME,
    SESSION_SECRET,
)

logger = logging.getLogger(__name__)


def generate_signed_session() -> Tuple[str, str]:
    """
    Generate a new random owner_id and its cryptographic signature.
    Returns: (owner_id, signed_token)
    """
    owner_id = str(uuid.uuid4())
    signature = _compute_signature(owner_id)
    token = f"{owner_id}.{signature}"
    return owner_id, token


def verify_session_token(token: Optional[str]) -> Optional[str]:
    """
    Validate an incoming session token.
    If valid, returns the verified owner_id.
    If invalid or absent, returns None. Never trusts raw input.
    """
    if not token or not isinstance(token, str) or "." not in token:
        return None

    parts = token.strip().split(".", 1)
    if len(parts) != 2:
        return None

    owner_id, provided_sig = parts
    # Ensure owner_id is a valid UUID string
    try:
        uuid.UUID(owner_id)
    except (ValueError, AttributeError):
        return None

    expected_sig = _compute_signature(owner_id)
    if hmac.compare_digest(provided_sig, expected_sig):
        return owner_id
    return None


def _compute_signature(value: str) -> str:
    """Compute HMAC-SHA256 signature for a value using SESSION_SECRET."""
    secret_bytes = SESSION_SECRET.encode("utf-8")
    return hmac.new(secret_bytes, value.encode("utf-8"), hashlib.sha256).hexdigest()


def get_authenticated_user_id(request: Request) -> Optional[str]:
    """Extract authenticated user ID from Authorization header or X-Auth-Token if present and valid."""
    from app.core.security import verify_access_token

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        auth_header = request.headers.get("X-Auth-Token")

    if auth_header:
        return verify_access_token(auth_header)
    return None


async def get_current_owner_id(request: Request, response: Response) -> str:
    """
    FastAPI dependency: Extract verified owner_id.
    Priority:
      1. Authenticated user ID (from Authorization: Bearer <token>)
      2. Verified anonymous session token (from X-Session-ID header or cookie)
      3. New signed anonymous session token (fallback)
    """
    # 1. Check for authenticated user token
    user_id = get_authenticated_user_id(request)
    if user_id:
        return user_id

    # 2. Check custom header (primary for API fetch calls)
    token = request.headers.get(SESSION_HEADER_NAME)

    # 3. Check cookie if header was not present
    if not token:
        token = request.cookies.get(SESSION_COOKIE_NAME)

    owner_id = verify_session_token(token)

    if not owner_id:
        owner_id, new_token = generate_signed_session()
        logger.debug("Issued new anonymous session owner: %s", owner_id)
        # Set response header and cookie
        response.headers[SESSION_HEADER_NAME] = new_token
        # Expose header to CORS client
        response.headers["Access-Control-Expose-Headers"] = SESSION_HEADER_NAME
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=new_token,
            httponly=False,  # Allow frontend JS client to read or let browser auto-send
            samesite="lax",
            max_age=60 * 60 * 24 * 365,  # 1 year
        )
    else:
        # Re-echo verified header so frontend client can keep it synchronized
        response.headers[SESSION_HEADER_NAME] = token
        response.headers["Access-Control-Expose-Headers"] = SESSION_HEADER_NAME

    return owner_id

