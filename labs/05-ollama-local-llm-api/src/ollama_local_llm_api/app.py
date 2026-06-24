from __future__ import annotations

from fastapi import FastAPI

from ollama_local_llm_api.ollama_client import OllamaClient
from ollama_local_llm_api.schemas import SummarizeRequest, SummarizeResponse
from ollama_local_llm_api.service import SummarizeService
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

SERVICE_NAME = "ollama-local-llm-api"
SERVICE_VERSION = "0.1.0"

configure_logging()
app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)

_service = SummarizeService(OllamaClient())


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    return await _service.summarize(request)
