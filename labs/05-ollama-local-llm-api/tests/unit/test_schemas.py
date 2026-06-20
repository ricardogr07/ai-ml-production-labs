from __future__ import annotations

import pytest
from pydantic import ValidationError

from ollama_local_llm_api.schemas import SummarizeRequest


@pytest.mark.unit
def test_summarize_request_valid() -> None:
    req = SummarizeRequest(text="Hello world.", model="llama3.2")
    assert req.model == "llama3.2"


@pytest.mark.unit
def test_summarize_request_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="")


@pytest.mark.unit
def test_summarize_request_rejects_invalid_max_tokens() -> None:
    with pytest.raises(ValidationError):
        SummarizeRequest(text="hello", max_tokens=0)
