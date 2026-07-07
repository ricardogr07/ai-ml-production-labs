"""End-to-end test: full graph run against the Anthropic API.

Skipped unless ANTHROPIC_API_KEY is set in the environment.
"""

from __future__ import annotations

import os

import pytest
from langgraph_project_agent import llm
from langgraph_project_agent.config import settings
from langgraph_project_agent.graph import build_graph
from langgraph_project_agent.llm import _TYPE_LABELS
from langgraph_project_agent.state import ProjectState

_IDEA = "A FastAPI RAG service on Azure with pytest coverage and a Dockerfile"


@pytest.fixture()
def anthropic_provider(monkeypatch):
    if not (os.environ.get("ANTHROPIC_API_KEY") or settings.anthropic_api_key):
        pytest.skip("ANTHROPIC_API_KEY not set (env var or .env)")
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    llm.get_chat_model.cache_clear()
    yield
    llm.get_chat_model.cache_clear()


@pytest.mark.e2e
@pytest.mark.usefixtures("anthropic_provider")
def test_graph_end_to_end_with_anthropic():
    result = build_graph().compile().invoke(ProjectState(project_idea=_IDEA))

    assert result["project_type"] in _TYPE_LABELS
    assert 0.0 <= result["thesis_score"] <= 1.0
    assert isinstance(result["implementation_plan"], str)
    assert result["implementation_plan"]
    scorecard = result["scorecard"]
    assert scorecard["recommendation"] in ("build it", "refine the idea")
