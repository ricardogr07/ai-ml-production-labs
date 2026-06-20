from __future__ import annotations

import pytest

from langgraph_project_agent.nodes import (
    classify_project_type,
    score_against_portfolio_thesis,
    identify_missing_artifacts,
    return_scorecard,
)
from langgraph_project_agent.state import ProjectState


@pytest.mark.unit
def test_classify_rag_project() -> None:
    state = ProjectState(project_idea="A RAG system with vector embeddings and retrieval.")
    result = classify_project_type(state)
    assert result.project_type == "rag_system"


@pytest.mark.unit
def test_classify_api_project() -> None:
    state = ProjectState(project_idea="A FastAPI endpoint with Azure deployment.")
    result = classify_project_type(state)
    assert result.project_type == "cloud_api"


@pytest.mark.unit
def test_classify_unknown_falls_back_to_general() -> None:
    state = ProjectState(project_idea="A website about cats.")
    result = classify_project_type(state)
    assert result.project_type == "general"


@pytest.mark.unit
def test_score_high_for_complete_idea() -> None:
    state = ProjectState(
        project_idea="FastAPI ML service with pytest tests, Docker, and Azure deployment.",
        project_type="cloud_api",
    )
    result = score_against_portfolio_thesis(state)
    assert result.thesis_score >= 0.6


@pytest.mark.unit
def test_return_scorecard_contains_recommendation() -> None:
    state = ProjectState(
        project_idea="FastAPI service",
        project_type="cloud_api",
        thesis_score=0.8,
        implementation_plan="1. scaffold",
    )
    result = return_scorecard(state)
    assert "recommendation" in result.scorecard
