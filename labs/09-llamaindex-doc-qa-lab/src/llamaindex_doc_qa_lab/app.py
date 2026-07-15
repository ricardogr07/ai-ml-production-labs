from __future__ import annotations

from fastapi import FastAPI

from llamaindex_doc_qa_lab.schemas import QueryRequest, QueryResponse
from llamaindex_doc_qa_lab.service import QueryService
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

SERVICE_NAME = "llamaindex-doc-qa-lab"
SERVICE_VERSION = "0.1.0"

configure_logging()
app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)

_service = QueryService()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    return _service.query(request)
