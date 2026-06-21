from __future__ import annotations

from fastapi import FastAPI

from fastapi_azure_ml_service.config import settings
from fastapi_azure_ml_service.schemas import PredictRequest, PredictResponse
from fastapi_azure_ml_service.service import PredictionService
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

configure_logging(settings.log_level)
app = FastAPI(title=settings.service_name, version=settings.service_version)
_service = PredictionService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=settings.service_name, version=settings.service_version)


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    return _service.predict(request)
