from __future__ import annotations

import json

import azure.functions as func
import pytest
from azure_functions_text_classifier.function_app import classify


def _make_request(body: dict[str, object]) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        body=json.dumps(body).encode(),
        url="/api/classify",
        headers={},
        params={},
    )


def _make_raw_request(raw: bytes) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        body=raw,
        url="/api/classify",
        headers={},
        params={},
    )


@pytest.mark.integration
def test_classify_incident() -> None:
    req = _make_request({"text": "Service crashed in production."})
    resp = classify(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data["label"] == "incident"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["model_version"]


@pytest.mark.integration
def test_classify_deployment() -> None:
    req = _make_request({"text": "New release deployed to staging."})
    resp = classify(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data["label"] == "deployment"


@pytest.mark.integration
def test_classify_general() -> None:
    req = _make_request({"text": "Routine team update."})
    resp = classify(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data["label"] == "general"


@pytest.mark.integration
def test_classify_rejects_empty_text() -> None:
    req = _make_request({"text": ""})
    resp = classify(req)
    assert resp.status_code == 422


@pytest.mark.integration
def test_classify_rejects_missing_text_field() -> None:
    req = _make_request({})
    resp = classify(req)
    assert resp.status_code == 422


@pytest.mark.integration
def test_classify_rejects_invalid_json() -> None:
    req = _make_raw_request(b"not valid json{{{")
    resp = classify(req)
    assert resp.status_code == 400
    data = json.loads(resp.get_body())
    assert "detail" in data
