from __future__ import annotations

import time

import httpx
from fastapi import FastAPI, HTTPException

from ollama_local_llm_api.ollama_client import OllamaClient
from ollama_local_llm_api.schemas import SummarizeRequest, SummarizeResponse
from production_labs_shared.health import HealthResponse
from production_labs_shared.logging import configure_logging

SERVICE_NAME = "ollama-local-llm-api"
SERVICE_VERSION = "0.1.0"

configure_logging()
app = FastAPI(title=SERVICE_NAME, version=SERVICE_VERSION)
_client = OllamaClient()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    prompt = f"Summarize the following text in 2-3 sentences:\n\n{request.text}"
    start = time.perf_counter()
    try:
        summary = await _client.generate(
            model=request.model, prompt=prompt, max_tokens=request.max_tokens
        )
    except httpx.ConnectError as err:
        raise HTTPException(
            status_code=503, detail="Ollama not reachable; is it running locally?"
        ) from err
    except httpx.TimeoutException as err:
        raise HTTPException(status_code=504, detail="Ollama request timed out.") from err
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return SummarizeResponse(summary=summary, model=request.model, latency_ms=latency_ms)
