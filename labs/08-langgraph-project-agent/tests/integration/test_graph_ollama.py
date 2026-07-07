"""Integration test: full graph run against a real local Ollama model."""

from __future__ import annotations

import pytest
from langgraph_project_agent.graph import build_graph
from langgraph_project_agent.llm import _TYPE_LABELS
from langgraph_project_agent.state import ProjectState

_IDEA = "A FastAPI RAG service on Azure with pytest coverage and a Dockerfile"


@pytest.mark.integration
@pytest.mark.usefixtures("ollama_provider")
def test_graph_end_to_end_with_ollama():
    result = build_graph().compile().invoke(ProjectState(project_idea=_IDEA))

    assert result["project_type"] in _TYPE_LABELS
    assert 0.0 <= result["thesis_score"] <= 1.0
    assert isinstance(result["implementation_plan"], str)
    assert result["implementation_plan"]
    scorecard = result["scorecard"]
    assert scorecard["recommendation"] in ("build it", "refine the idea")
