"""
FoodVerse AI — Authentication & User Profile Routes.

Endpoints:
  - POST /api/v1/auth/signup: Register new user (name, email, birthday, password)
  - POST /api/v1/auth/login: Authenticate user with email and password
  - GET  /api/v1/auth/me: Fetch current authenticated user's profile and stats
  - POST /api/v1/auth/logout: Client session termination helper
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from app.core.config import SESSION_HEADER_NAME
from app.core.security import create_access_token, hash_password, verify_password
from app.core.session import get_authenticated_user_id, verify_session_token
from app.db.user_repository import user_repository
from app.schemas.auth import (
    AuthResponse,
    UserLoginRequest,
    UserProfileResponse,
    UserSignupRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/auth/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with email, name, birthday, and password",
)
async def signup(
    body: UserSignupRequest,
    request: Request,
    response: Response,
) -> AuthResponse:
    """Create a new user profile and return signed access token."""
    clean_email = body.email.strip().lower()

    # Check if user already exists
    existing = await user_repository.get_user_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_TAKEN", "message": f"An account with email '{clean_email}' already exists. Please log in."}},
        )

    # Hash password securely
    pwd_hash = hash_password(body.password)

    try:
        user_doc = await user_repository.create_user(
            name=body.name.strip(),
            email=clean_email,
            birthday=body.birthday.strip(),
            password_hash=pwd_hash,
        )
    except Exception as exc:
        logger.error("Signup failed for %s: %s", clean_email, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DATABASE_ERROR", "message": "Failed to create user account."}},
        )

    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DATABASE_UNAVAILABLE", "message": "User database service is currently unavailable."}},
        )

    user_id = str(user_doc["id"])
    token = create_access_token(user_id)

    # Automatically claim any guest reports from the current anonymous session
    anon_token = request.headers.get(SESSION_HEADER_NAME)
    anon_owner_id = verify_session_token(anon_token) if anon_token else None
    if anon_owner_id:
        await user_repository.claim_session_reports(anon_owner_id, user_id)

    stats = await user_repository.get_user_stats(user_id)
    user_doc["stats"] = stats

    return AuthResponse(
        status="success",
        token=token,
        user=UserProfileResponse(**user_doc),
        message="Account created successfully! Welcome to FoodVerse AI.",
    )


@router.post(
    "/auth/login",
    response_model=AuthResponse,
    summary="Log in with email and password",
)
async def login(
    body: UserLoginRequest,
    request: Request,
) -> AuthResponse:
    """Authenticate user credentials and issue signed token."""
    clean_email = body.email.strip().lower()
    raw_user = await user_repository.get_user_by_email(clean_email)

    if not raw_user or not raw_user.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Incorrect email or password."}},
        )

    if not verify_password(body.password, raw_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Incorrect email or password."}},
        )

    user_id = str(raw_user["id"])
    token = create_access_token(user_id)

    # Claim guest reports if user performed work anonymously before logging in
    anon_token = request.headers.get(SESSION_HEADER_NAME)
    anon_owner_id = verify_session_token(anon_token) if anon_token else None
    if anon_owner_id:
        await user_repository.claim_session_reports(anon_owner_id, user_id)

    # Strip hash
    raw_user.pop("password_hash", None)
    stats = await user_repository.get_user_stats(user_id)
    raw_user["stats"] = stats

    return AuthResponse(
        status="success",
        token=token,
        user=UserProfileResponse(**raw_user),
        message="Logged in successfully.",
    )


@router.get(
    "/auth/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user's profile and activity stats",
)
async def get_my_profile(request: Request) -> UserProfileResponse:
    """Retrieve personal data for the logged-in user."""
    user_id = get_authenticated_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "NOT_AUTHENTICATED", "message": "Please log in to view your profile data."}},
        )

    user_doc = await user_repository.get_user_by_id(user_id)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": "User account could not be found."}},
        )

    stats = await user_repository.get_user_stats(user_id)
    user_doc["stats"] = stats

    return UserProfileResponse(**user_doc)


@router.post(
    "/auth/logout",
    summary="Log out of session",
)
async def logout() -> dict:
    """Informational logout endpoint; clients clear local storage token."""
    return {"status": "success", "message": "Logged out successfully."}
