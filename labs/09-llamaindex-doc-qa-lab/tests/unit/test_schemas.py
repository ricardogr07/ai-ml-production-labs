from __future__ import annotations

import pytest
from llamaindex_doc_qa_lab.schemas import QueryRequest, QueryResponse, SourceChunk
from pydantic import ValidationError


@pytest.mark.unit
def test_query_request_valid() -> None:
    req = QueryRequest(question="What does lab 01 prove?")
    assert req.top_k == 3


@pytest.mark.unit
def test_query_request_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        QueryRequest(question="")


@pytest.mark.unit
def test_query_response_serializes() -> None:
    resp = QueryResponse(
        answer="It proves cloud API deployment.",
        sources=[SourceChunk(content="Lab 01 deploys to Azure.", source="README.md", score=0.9)],
    )
    data = resp.model_dump()
    assert "answer" in data
    assert len(data["sources"]) == 1
