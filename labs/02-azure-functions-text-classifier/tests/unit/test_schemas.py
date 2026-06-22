from __future__ import annotations

import pytest
from azure_functions_text_classifier.schemas import ClassifyRequest, ClassifyResponse
from pydantic import ValidationError


@pytest.mark.unit
def test_classify_request_valid() -> None:
    req = ClassifyRequest(text="Service crashed in production.")
    assert req.text == "Service crashed in production."


@pytest.mark.unit
def test_classify_request_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        ClassifyRequest(text="")


@pytest.mark.unit
def test_classify_request_rejects_text_over_limit() -> None:
    with pytest.raises(ValidationError):
        ClassifyRequest(text="x" * 10_001)


@pytest.mark.unit
def test_classify_response_valid() -> None:
    resp = ClassifyResponse(label="incident", confidence=0.85, model_version="rules-v0.1.0")
    assert resp.label == "incident"
    assert resp.confidence == 0.85


@pytest.mark.unit
def test_classify_response_rejects_confidence_above_one() -> None:
    with pytest.raises(ValidationError):
        ClassifyResponse(label="incident", confidence=1.5, model_version="rules-v0.1.0")


@pytest.mark.unit
def test_classify_response_rejects_confidence_below_zero() -> None:
    with pytest.raises(ValidationError):
        ClassifyResponse(label="incident", confidence=-0.1, model_version="rules-v0.1.0")
