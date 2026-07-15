from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from llamaindex_doc_qa_lab import readiness
from llamaindex_doc_qa_lab.errors import GenerationError, NotReadyError
from llamaindex_doc_qa_lab.schemas import QueryRequest, QueryResponse
from llamaindex_doc_qa_lab.service import QueryService
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

SERVICE_NAME = "llamaindex-doc-qa-lab"
SERVICE_VERSION = "0.1.0"

configure_logging()
app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)

_service = QueryService()


@app.exception_handler(NotReadyError)
def _handle_not_ready(_request: Request, exc: NotReadyError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(GenerationError)
def _handle_generation_error(_request: Request, exc: GenerationError) -> JSONResponse:
    return JSONResponse(status_code=424, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.get("/ready")
def ready() -> JSONResponse:
    checks = readiness.readiness()
    ok = all(status == "ok" for status in checks.values())
    return JSONResponse(status_code=200 if ok else 503, content={"ready": ok, "checks": checks})


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return _service.query(request)
