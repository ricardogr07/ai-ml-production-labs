"""End-to-end test: full query flow against the Anthropic API.

Skipped unless ANTHROPIC_API_KEY is set in the environment.
"""

from __future__ import annotations

import os

import pytest
from llamaindex_doc_qa_lab import llm
from llamaindex_doc_qa_lab.config import settings
from llamaindex_doc_qa_lab.schemas import QueryRequest
from llamaindex_doc_qa_lab.service import QueryService


@pytest.fixture()
def anthropic_provider(monkeypatch):
    if not (os.environ.get("ANTHROPIC_API_KEY") or settings.anthropic_api_key):
        pytest.skip("ANTHROPIC_API_KEY not set (env var or .env)")
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    llm.get_llm.cache_clear()
    yield
    llm.get_llm.cache_clear()


@pytest.mark.e2e
@pytest.mark.usefixtures("seeded_qdrant", "anthropic_provider")
def test_query_end_to_end_with_anthropic():
    result = QueryService().query(QueryRequest(question="What is DNA?", top_k=2))

    assert result.answer
    # Retrieval must have contributed: a truthy answer with zero sources would
    # mean the LLM answered without the corpus, which is not the loop under test.
    assert 0 < len(result.sources) <= 2
    assert all(source.content for source in result.sources)
