"""
FoodVerse AI — Anonymous Session & History API Route Tests.

Tests:
  - HMAC session generation and signature verification
  - Automatic session issuance and header propagation
  - Owner-scoped history summary, listing, detail, and delete
  - Owner-scoped media streaming
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from starlette.testclient import TestClient

from app.core.session import (
    generate_signed_session,
    verify_session_token,
)
from app.db.media_repository import media_repository
from app.db.report_repository import report_repository
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Session Cryptographic Verification Tests
# ---------------------------------------------------------------------------
def test_signed_session_generation_and_verification():
    owner_id, token = generate_signed_session()
    assert owner_id in token
    assert "." in token

    # Verification of valid token
    verified = verify_session_token(token)
    assert verified == owner_id

    # Tampered token fails
    tampered = token[:-4] + "abcd"
    assert verify_session_token(tampered) is None

    # Invalid formats
    assert verify_session_token("not-a-token") is None
    assert verify_session_token(None) is None
    assert verify_session_token("123.456") is None


# ---------------------------------------------------------------------------
# 2. Session Header Auto-Issuance in API Requests
# ---------------------------------------------------------------------------
def test_api_issues_new_session_when_missing(client):
    resp = client.get("/api/v1/history/summary")
    assert resp.status_code == 200
    assert "X-Session-ID" in resp.headers
    issued_token = resp.headers["X-Session-ID"]
    assert verify_session_token(issued_token) is not None


def test_api_preserves_valid_session(client):
    owner_id, token = generate_signed_session()
    resp = client.get("/api/v1/history/summary", headers={"X-Session-ID": token})
    assert resp.status_code == 200
    assert resp.headers.get("X-Session-ID") == token


# ---------------------------------------------------------------------------
# 3. History Endpoints & Isolation Tests
# ---------------------------------------------------------------------------
def test_history_summary_endpoint(client):
    owner_id, token = generate_signed_session()
    mock_summary = {
        "total_reports": 3,
        "counts_by_feature": {
            "food_recognition": 1,
            "freshness_analysis": 1,
            "hygiene_analysis": 1,
            "recipe_generation": 0,
            "meal_plan": 0,
        },
        "recent_reports": [],
    }

    with patch.object(report_repository, "get_dashboard_summary", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_summary
        resp = client.get("/api/v1/history/summary", headers={"X-Session-ID": token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["total_reports"] == 3
        # Assert repository was called with the verified owner_id from token
        mock_get.assert_called_once_with(owner_id)


def test_history_list_endpoint_pagination_and_filter(client):
    owner_id, token = generate_signed_session()
    mock_list_result = {
        "items": [{"id": str(ObjectId()), "feature": "food_recognition"}],
        "next_cursor": str(ObjectId()),
        "has_more": True,
        "total": 5,
    }

    with patch.object(report_repository, "list_reports", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_list_result
        resp = client.get(
            "/api/v1/history?feature=food_recognition&limit=5",
            headers={"X-Session-ID": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert len(data["items"]) == 1
        assert data["has_more"] is True
        mock_list.assert_called_once_with(
            owner_id=owner_id,
            feature="food_recognition",
            status=None,
            limit=5,
            cursor=None,
        )


def test_history_get_report_returns_404_when_unauthorized(client):
    owner_id, token = generate_signed_session()
    fake_id = str(ObjectId())

    # Mock get_report returning None (due to mismatch or not found)
    with patch.object(report_repository, "get_report", new_callable=AsyncMock, return_value=None):
        resp = client.get(f"/api/v1/history/{fake_id}", headers={"X-Session-ID": token})
        assert resp.status_code == 404


def test_history_delete_returns_404_when_unauthorized(client):
    owner_id, token = generate_signed_session()
    fake_id = str(ObjectId())

    # Mock delete_report returning False
    with patch.object(report_repository, "delete_report", new_callable=AsyncMock, return_value=False):
        resp = client.delete(f"/api/v1/history/{fake_id}", headers={"X-Session-ID": token})
        assert resp.status_code == 404


def test_media_get_returns_404_when_unauthorized(client):
    owner_id, token = generate_signed_session()
    fake_file_id = str(ObjectId())

    # Mock get_image returning None
    with patch.object(media_repository, "get_image", new_callable=AsyncMock, return_value=None):
        resp = client.get(f"/api/v1/media/{fake_file_id}", headers={"X-Session-ID": token})
        assert resp.status_code == 404
