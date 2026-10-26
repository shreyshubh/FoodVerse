"""
FoodVerse AI — Hygiene & Safety Detector Tests.
"""
import io
import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.hygiene_detector import hygiene_detector_service


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def create_test_image_bytes():
    img = Image.new("RGB", (320, 240), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_hygiene_models_loaded_and_classes_verified():
    """Ensure YOLO models are loaded and verified for target classes."""
    assert hygiene_detector_service.is_ready is True
    assert hygiene_detector_service.ppe_model is not None
    # Verify exact classes in PPE model
    names = hygiene_detector_service.ppe_model.names
    # Expected classes in keremberke/yolov8n-protective-equipment-detection:
    expected_classes = {"glove", "no_glove", "mask", "no_mask", "helmet", "no_helmet"}
    assert expected_classes.issubset(set(names.values()))


def test_hygiene_no_person_detected_is_not_assessable(client):
    """An empty scene contains no people. Score must be None and status NOT ASSESSABLE, never a fake 100%."""
    img_bytes = create_test_image_bytes()
    resp = client.post(
        "/api/v1/hygiene-analysis",
        files={"media": ("station.jpg", img_bytes, "image/jpeg")},
        data={"station_id": "Grill Station 02"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "no_person_detected"
    assert data["overall_score"] is None
    assert data["risk_level"] == "NOT ASSESSABLE"
    assert data["persons_observed"] == 0
    assert data["compliance_breakdown"]["gloves"] is None
    assert data["compliance_breakdown"]["hairnets"] is None
    assert data["compliance_breakdown"]["masks"] is None
    assert "NOT ASSESSABLE" in data["audit_report_text"]


def test_hygiene_empty_file_rejected(client):
    resp = client.post(
        "/api/v1/hygiene-analysis",
        files={"media": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 400


def test_hygiene_scoring_when_person_and_violations_detected():
    """When personnel are observed, compliance scores and risk levels are deterministically computed."""
    img_bytes = create_test_image_bytes()

    # Simulate base model detecting 1 person and PPE model detecting no_glove
    mock_base_box = MagicMock()
    mock_base_box.cls = [0]  # person
    mock_base_result = MagicMock()
    mock_base_result.boxes = [mock_base_box]

    mock_ppe_box = MagicMock()
    mock_ppe_box.cls = [4]  # no_glove
    mock_ppe_box.conf = [0.85]
    mock_ppe_box.xyxy = [[10.0, 10.0, 50.0, 50.0]]
    mock_ppe_result = MagicMock()
    mock_ppe_result.boxes = [mock_ppe_box]

    with patch.object(hygiene_detector_service.base_model, "predict", return_value=[mock_base_result]), \
         patch.object(hygiene_detector_service.ppe_model, "predict", return_value=[mock_ppe_result]):
        resp = hygiene_detector_service.inspect_media(img_bytes, is_video=False, station_id="prep_line_01")
        assert resp.status == "success"
        assert resp.persons_observed == 1
        assert resp.overall_score is not None
        assert 0 <= resp.overall_score <= 100
        assert resp.risk_level in {"LOW RISK", "MODERATE RISK", "HIGH RISK"}
        assert len(resp.alerts) == 1
        assert resp.alerts[0].violation_type == "no_gloves"
