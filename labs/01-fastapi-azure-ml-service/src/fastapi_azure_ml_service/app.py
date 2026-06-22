from __future__ import annotations

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from fastapi_azure_ml_service.config import settings
from fastapi_azure_ml_service.schemas import PredictRequest, PredictResponse
from fastapi_azure_ml_service.service import PredictionService
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

configure_logging(settings.log_level)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.service_name, version=settings.service_version)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_service = PredictionService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=settings.service_name, version=settings.service_version)


@app.post("/predict", response_model=PredictResponse)
@limiter.limit("10/minute")
def predict(request: Request, body: PredictRequest) -> PredictResponse:  # noqa: ARG001
    return _service.predict(body)
