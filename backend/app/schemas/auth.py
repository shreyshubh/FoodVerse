"""
FoodVerse AI — Authentication Schemas.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name")
    email: str = Field(..., description="User email address")
    birthday: str = Field(..., description="Birthday in YYYY-MM-DD format")
    password: str = Field(..., min_length=6, max_length=128, description="Password (minimum 6 characters)")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean):
            raise ValueError("Birthday must be in YYYY-MM-DD format.")
        return clean


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email address format.")
        return clean


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    birthday: str
    created_at: str
    stats: Optional[Dict[str, Any]] = None


class AuthResponse(BaseModel):
    status: str = "success"
    token: str
    user: UserProfileResponse
    message: str = "Authenticated successfully."
