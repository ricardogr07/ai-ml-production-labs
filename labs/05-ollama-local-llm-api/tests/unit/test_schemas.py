from __future__ import annotations

import pytest
from ollama_local_llm_api.schemas import SummarizeRequest, SummarizeResponse
from pydantic import ValidationError


@pytest.mark.unit
def test_summarize_request_valid() -> None:
    req = SummarizeRequest(text="Hello world.", model="phi3.5")
    assert req.model == "phi3.5"


@pytest.mark.unit
def test_summarize_request_default_model() -> None:
    req = SummarizeRequest(text="Hello world.")
    assert req.model == "phi3.5"


@pytest.mark.unit
def test_summarize_request_default_max_tokens() -> None:
    req = SummarizeRequest(text="Hello world.")
    assert req.max_tokens == 256


@pytest.mark.unit
def test_summarize_request_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="")


@pytest.mark.unit
def test_summarize_request_rejects_invalid_max_tokens() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="hello", max_tokens=0)


@pytest.mark.unit
def test_summarize_request_rejects_max_tokens_above_limit() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="hello", max_tokens=2049)


@pytest.mark.unit
def test_summarize_request_accepts_max_tokens_boundary() -> None:
    req = SummarizeRequest(text="hello", max_tokens=2048)
    assert req.max_tokens == 2048


@pytest.mark.unit
def test_summarize_response_fields() -> None:
    resp = SummarizeResponse(summary="Short result.", model="phi3.5", latency_ms=42.5)
    assert resp.summary == "Short result."
    assert resp.model == "phi3.5"
    assert resp.latency_ms == 42.5
