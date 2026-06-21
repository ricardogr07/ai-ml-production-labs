from __future__ import annotations

import pytest
from fastapi_azure_ml_service.schemas import PredictRequest, PredictResponse
from pydantic import ValidationError


@pytest.mark.unit
def test_predict_request_valid() -> None:
    req = PredictRequest(text="The deployment failed.")
    assert req.text == "The deployment failed."


@pytest.mark.unit
def test_predict_request_rejects_empty_text() -> None:
    with pytest.raises(ValidationError):
        PredictRequest(text="")


@pytest.mark.unit
def test_predict_response_valid() -> None:
    resp = PredictResponse(label="incident", confidence=0.85, model_version="rules-v0.1.0")
    assert resp.label == "incident"
    assert resp.confidence == 0.85


@pytest.mark.unit
def test_predict_response_rejects_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        PredictResponse(label="incident", confidence=1.5, model_version="rules-v0.1.0")
