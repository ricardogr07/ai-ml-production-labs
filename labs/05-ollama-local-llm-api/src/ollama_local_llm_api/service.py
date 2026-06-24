from __future__ import annotations

import time

import httpx
from fastapi import HTTPException

from ollama_local_llm_api.ollama_client import OllamaClient
from ollama_local_llm_api.schemas import SummarizeRequest, SummarizeResponse


class SummarizeService:
    def __init__(self, client: OllamaClient) -> None:
        self._client = client

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        prompt = f"Summarize the following text in 2-3 sentences:\n\n{request.text}"
        start = time.perf_counter()
        try:
            summary = await self._client.generate(
                model=request.model,
                prompt=prompt,
                max_tokens=request.max_tokens,
            )
        except httpx.ConnectError as err:
            raise HTTPException(
                status_code=503, detail="Ollama not reachable; is it running locally?"
            ) from err
        except httpx.TimeoutException as err:
            raise HTTPException(status_code=504, detail="Ollama request timed out.") from err
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return SummarizeResponse(summary=summary, model=request.model, latency_ms=latency_ms)
