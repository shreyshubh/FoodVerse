"""
FoodVerse AI — Authentication & User Profile Test Suite.

Tests registration, password hashing, login, token verification,
profile retrieval, and anonymous report claiming.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import hash_password, verify_password, create_access_token, verify_access_token


@pytest.fixture
def client():
    return TestClient(app)


def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123"
    hashed = hash_password(raw_pwd)
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_validation():
    user_id = "test-user-id-999"
    token = create_access_token(user_id)
    assert token.startswith("auth.test-user-id-999.")
    extracted = verify_access_token(token)
    assert extracted == user_id
    # Test with Bearer prefix
    assert verify_access_token(f"Bearer {token}") == user_id
    # Test invalid signature
    assert verify_access_token(token + "tampered") is None


def test_signup_validation_errors(client):
    # Short password
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Alex",
            "email": "alex@example.com",
            "birthday": "2000-01-01",
            "password": "123",
        },
    )
    assert res.status_code == 422

    # Invalid birthday format
    res2 = client.post(
        "/api/v1/auth/signup",
        json={
            "name": "Alex",
            "email": "alex@example.com",
            "birthday": "01/01/2000",
            "password": "validPassword123",
        },
    )
    assert res2.status_code == 422


def test_auth_me_requires_authentication(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
