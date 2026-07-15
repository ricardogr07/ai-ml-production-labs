"""Unit tests for QueryService: top_k propagation and response mapping."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from llamaindex_doc_qa_lab.schemas import QueryRequest
from llamaindex_doc_qa_lab.service import QueryService


class _FakeNode:
    def __init__(self, content: str, source: str) -> None:
        self._content = content
        self.metadata = {"source": source}

    def get_content(self) -> str:
        return self._content


class _FakeSourceNode:
    def __init__(self, content: str, source: str, score: float) -> None:
        self.node = _FakeNode(content, source)
        self.score = score


class _FakeResponse:
    def __init__(self, answer: str, source_nodes: list[_FakeSourceNode]) -> None:
        self._answer = answer
        self.source_nodes = source_nodes

    def __str__(self) -> str:
        return self._answer


@pytest.mark.unit
def test_query_maps_response_to_schema_and_applies_top_k():
    fake_response = _FakeResponse(
        "Paris.", [_FakeSourceNode("Paris is the capital of France.", "France", 0.9)]
    )
    mock_query_engine = MagicMock()
    mock_query_engine.query.return_value = fake_response
    mock_index = MagicMock()
    mock_index.as_query_engine.return_value = mock_query_engine

    with (
        patch(
            "llamaindex_doc_qa_lab.service.VectorStoreIndex.from_vector_store",
            return_value=mock_index,
        ),
        patch("llamaindex_doc_qa_lab.service.vector_store.get_vector_store"),
        patch("llamaindex_doc_qa_lab.service.embeddings.get_embedding_model"),
        patch("llamaindex_doc_qa_lab.service.llm.get_llm"),
    ):
        result = QueryService().query(
            QueryRequest(question="What is the capital of France?", top_k=2)
        )

    assert result.answer == "Paris."
    assert len(result.sources) == 1
    assert result.sources[0].content == "Paris is the capital of France."
    assert result.sources[0].source == "France"
    assert result.sources[0].score == 0.9

    _, kwargs = mock_index.as_query_engine.call_args
    assert kwargs["similarity_top_k"] == 2
