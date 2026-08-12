from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from finetune_project_classifier import readiness, service
from finetune_project_classifier.errors import ModelNotReadyError
from finetune_project_classifier.schemas import ProjectRequest, ProjectResponse
from production_labs_shared.health import HealthResponse

SERVICE_NAME = "finetune-project-classifier"
app = FastAPI(title=SERVICE_NAME, version="0.1.0")


@app.exception_handler(ModelNotReadyError)
def model_not_ready(_request: Request, exc: ModelNotReadyError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version="0.1.0")


@app.get("/ready")
def ready() -> JSONResponse:
    checks = readiness.readiness()
    ok = all(value == "ok" for value in checks.values())
    return JSONResponse(status_code=200 if ok else 503, content={"ready": ok, "checks": checks})


@app.post("/predict", response_model=ProjectResponse)
def predict(request: ProjectRequest) -> ProjectResponse:
    return service.predict(request)
