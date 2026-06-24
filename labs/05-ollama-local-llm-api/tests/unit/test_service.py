from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from ollama_local_llm_api.schemas import SummarizeRequest
from ollama_local_llm_api.service import SummarizeService


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.generate = AsyncMock(return_value="Short summary.")
    return client


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_returns_response(mock_client: MagicMock) -> None:
    service = SummarizeService(mock_client)
    resp = await service.summarize(SummarizeRequest(text="Some long text."))
    assert resp.summary == "Short summary."
    assert resp.model == "phi3.5"
    assert resp.latency_ms >= 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_passes_model_to_client(mock_client: MagicMock) -> None:
    service = SummarizeService(mock_client)
    await service.summarize(SummarizeRequest(text="Text.", model="tinyllama"))
    _, kwargs = mock_client.generate.call_args
    assert kwargs["model"] == "tinyllama"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_passes_max_tokens_to_client(mock_client: MagicMock) -> None:
    service = SummarizeService(mock_client)
    await service.summarize(SummarizeRequest(text="Text.", max_tokens=64))
    _, kwargs = mock_client.generate.call_args
    assert kwargs["max_tokens"] == 64


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_prompt_contains_input_text(mock_client: MagicMock) -> None:
    service = SummarizeService(mock_client)
    await service.summarize(SummarizeRequest(text="unique_marker_text"))
    _, kwargs = mock_client.generate.call_args
    assert "unique_marker_text" in kwargs["prompt"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_raises_503_on_connect_error(mock_client: MagicMock) -> None:
    import httpx

    mock_client.generate = AsyncMock(side_effect=httpx.ConnectError("refused"))
    service = SummarizeService(mock_client)
    with pytest.raises(HTTPException) as exc_info:
        await service.summarize(SummarizeRequest(text="Text."))
    assert exc_info.value.status_code == 503


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarize_raises_504_on_timeout(mock_client: MagicMock) -> None:
    import httpx

    mock_client.generate = AsyncMock(side_effect=httpx.TimeoutException("timed out"))
    service = SummarizeService(mock_client)
    with pytest.raises(HTTPException) as exc_info:
        await service.summarize(SummarizeRequest(text="Text."))
    assert exc_info.value.status_code == 504
