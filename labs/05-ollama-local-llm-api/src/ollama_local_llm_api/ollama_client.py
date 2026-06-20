"""Thin async client for the local Ollama API."""

from __future__ import annotations

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 30.0) -> None:
        self._base_url = base_url
        self._timeout = timeout

    async def generate(self, model: str, prompt: str, max_tokens: int = 256) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/generate", json=payload)
            response.raise_for_status()
            return str(response.json().get("response", ""))
