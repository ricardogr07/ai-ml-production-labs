from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mlflow_classifier_api import readiness, service
from mlflow_classifier_api.errors import ModelNotReady
from mlflow_classifier_api.schemas import IncidentFeatures, SeverityResponse
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

SERVICE_NAME = "mlflow-classifier-api"
SERVICE_VERSION = "0.1.0"

configure_logging()
app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)


@app.exception_handler(ModelNotReady)
def _handle_model_not_ready(_request: Request, exc: ModelNotReady) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/ready")
def ready() -> JSONResponse:
    checks = readiness.readiness()
    ok = all(status == "ok" for status in checks.values())
    return JSONResponse(status_code=200 if ok else 503, content={"ready": ok, "checks": checks})


@app.post("/predict", response_model=SeverityResponse)
def predict(features: IncidentFeatures) -> SeverityResponse:
    return service.predict(features)
