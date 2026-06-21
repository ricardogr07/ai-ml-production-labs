from __future__ import annotations

import pytest
from fastapi_azure_ml_service.schemas import PredictRequest
from fastapi_azure_ml_service.service import PredictionService


@pytest.fixture
def service() -> PredictionService:
    return PredictionService()


@pytest.mark.unit
def test_predict_incident_on_error_keyword(service: PredictionService) -> None:
    response = service.predict(PredictRequest(text="The deployment failed."))

    assert response.label == "incident"
    assert response.confidence >= 0.8


@pytest.mark.unit
def test_predict_incident_on_timeout_keyword(service: PredictionService) -> None:
    response = service.predict(PredictRequest(text="Service timeout detected."))

    assert response.label == "incident"


@pytest.mark.unit
def test_predict_deployment_label(service: PredictionService) -> None:
    response = service.predict(PredictRequest(text="New release going out tonight."))

    assert response.label == "deployment"


@pytest.mark.unit
def test_predict_general_label(service: PredictionService) -> None:
    response = service.predict(PredictRequest(text="Routine status update."))

    assert response.label == "general"


@pytest.mark.unit
def test_predict_returns_model_version(service: PredictionService) -> None:
    response = service.predict(PredictRequest(text="Anything."))

    assert response.model_version.startswith("rules-")
