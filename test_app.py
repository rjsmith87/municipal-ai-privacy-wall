"""Tests for the Municipal AI Privacy Wall Flask application."""
import base64
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from PIL import Image

from app import app, parse_create_case_block, preprocess_for_yolo, get_head_regions


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _make_test_image_b64(width=100, height=100):
    """Helper: create a minimal JPEG image encoded as base64."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# --- Test 1: /health returns 200 with expected keys ---
def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert "models" in data
    assert "mediapipe_face" in data["models"]


# --- Test 2: /redact with missing body returns 400 ---
def test_redact_missing_body(client):
    resp = client.post("/redact", data="", content_type="application/json")
    assert resp.status_code == 400


# --- Test 3: /redact with missing imageBase64 returns 400 ---
def test_redact_missing_image_field(client):
    resp = client.post("/redact", json={"foo": "bar"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


# --- Test 4: parse_create_case_block extracts fields correctly ---
def test_parse_create_case_block_valid():
    text = (
        "Some intro text\n"
        "[CREATE_CASE]\n"
        "subject: Pothole on Main St\n"
        "description: Large pothole near intersection\n"
        "category: Roads\n"
        "priority: High\n"
        "[/CREATE_CASE]\n"
        "Some closing text"
    )
    result = parse_create_case_block(text)
    assert result is not None
    assert result["subject"] == "Pothole on Main St"
    assert result["description"] == "Large pothole near intersection"
    assert result["category"] == "Roads"
    assert result["priority"] == "High"


def test_parse_create_case_block_missing():
    result = parse_create_case_block("No case block here")
    assert result is None


# --- Test 5: preprocess_for_yolo produces correct tensor shape ---
def test_preprocess_for_yolo_shape():
    fake_bgr = np.zeros((480, 640, 3), dtype=np.uint8)
    blob, scale, pad_x, pad_y = preprocess_for_yolo(fake_bgr, input_size=640)
    assert blob.shape == (1, 3, 640, 640)
    assert blob.dtype == np.float32
    assert 0.0 <= blob.max() <= 1.0


# --- Test 6: get_head_regions skips persons that already have a face ---
def test_get_head_regions_skips_covered():
    persons = [(100, 100, 200, 400)]
    faces = [(120, 110, 180, 170)]  # face inside person's head area
    heads = get_head_regions(persons, faces)
    assert len(heads) == 0, "Should not create a fallback head when a face is detected"


def test_get_head_regions_returns_head_when_no_face():
    persons = [(100, 100, 200, 400)]
    faces = []
    heads = get_head_regions(persons, faces)
    assert len(heads) == 1


# --- Test 7: /redact with a valid image returns redaction metadata ---
def test_redact_valid_image(client):
    image_b64 = _make_test_image_b64()
    resp = client.post("/redact", json={"imageBase64": image_b64})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "redactedBase64" in data
    assert "facesBlurred" in data
    assert "platesBlurred" in data
    assert "vehiclesDetected" in data
