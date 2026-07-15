"""Integration test: full query flow against a real local Ollama + seeded Qdrant."""

from __future__ import annotations

import pytest
from llamaindex_doc_qa_lab.schemas import QueryRequest
from llamaindex_doc_qa_lab.service import QueryService


@pytest.mark.integration
@pytest.mark.usefixtures("seeded_qdrant", "ollama_provider")
def test_query_end_to_end_with_ollama():
    result = QueryService().query(QueryRequest(question="What is DNA?", top_k=2))

    assert result.answer
    assert len(result.sources) <= 2
    assert all(source.content for source in result.sources)
