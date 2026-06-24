from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from ollama_local_llm_api.app import app
from ollama_local_llm_api.schemas import SummarizeResponse

_PATCH_TARGET = "ollama_local_llm_api.app._service.summarize"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.integration
def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ollama-local-llm-api"
    assert "version" in data
    assert "timestamp_utc" in data


@pytest.mark.integration
def test_summarize_success(client: TestClient) -> None:
    mock_resp = SummarizeResponse(summary="A concise summary.", model="phi3.5", latency_ms=50.0)
    with patch(_PATCH_TARGET, new=AsyncMock(return_value=mock_resp)):
        response = client.post(
            "/summarize",
            json={"text": "FastAPI is a modern Python web framework.", "model": "phi3.5"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "A concise summary."
    assert data["model"] == "phi3.5"
    assert data["latency_ms"] >= 0


@pytest.mark.integration
def test_summarize_returns_model_from_request(client: TestClient) -> None:
    mock_resp = SummarizeResponse(summary="Result.", model="tinyllama", latency_ms=10.0)
    with patch(_PATCH_TARGET, new=AsyncMock(return_value=mock_resp)):
        response = client.post("/summarize", json={"text": "Some text.", "model": "tinyllama"})
    assert response.status_code == 200
    assert response.json()["model"] == "tinyllama"


@pytest.mark.integration
def test_summarize_503_when_ollama_unreachable(client: TestClient) -> None:
    exc = HTTPException(status_code=503, detail="Ollama not reachable; is it running locally?")
    with patch(_PATCH_TARGET, new=AsyncMock(side_effect=exc)):
        response = client.post("/summarize", json={"text": "Some text."})
    assert response.status_code == 503
    assert "Ollama not reachable" in response.json()["detail"]


@pytest.mark.integration
def test_summarize_504_on_timeout(client: TestClient) -> None:
    exc = HTTPException(status_code=504, detail="Ollama request timed out.")
    with patch(_PATCH_TARGET, new=AsyncMock(side_effect=exc)):
        response = client.post("/summarize", json={"text": "Some text."})
    assert response.status_code == 504


@pytest.mark.integration
def test_summarize_rejects_empty_text(client: TestClient) -> None:
    response = client.post("/summarize", json={"text": ""})
    assert response.status_code == 422


@pytest.mark.integration
def test_summarize_rejects_missing_text(client: TestClient) -> None:
    response = client.post("/summarize", json={})
    assert response.status_code == 422


@pytest.mark.integration
def test_summarize_rejects_max_tokens_zero(client: TestClient) -> None:
    response = client.post("/summarize", json={"text": "hello", "max_tokens": 0})
    assert response.status_code == 422
