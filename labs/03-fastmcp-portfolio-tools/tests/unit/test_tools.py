from __future__ import annotations

import pytest
from fastmcp_portfolio_tools.server import (
    generate_portfolio_summary,
    score_project,
    suggest_readme_sections,
)


@pytest.mark.unit
def test_score_project_all_criteria_match() -> None:
    result = score_project("FastAPI ML service with pytest, Azure deployment, and Docker.")
    assert result.score == 1.0
    assert result.recommendation == "strong"
    assert all(result.criteria.values())


@pytest.mark.unit
def test_score_project_high_score() -> None:
    result = score_project("FastAPI service with pytest and Azure.")
    assert result.score >= 0.6
    assert result.recommendation == "strong"


@pytest.mark.unit
def test_score_project_low_score() -> None:
    result = score_project("A simple script.")
    assert result.score < 0.6
    assert result.recommendation == "needs work"


@pytest.mark.unit
def test_score_project_has_api_criterion() -> None:
    result = score_project("REST endpoint service.")
    assert result.criteria["has_api"] is True
    result2 = score_project("No web interface here.")
    assert result2.criteria["has_api"] is False


@pytest.mark.unit
def test_score_project_has_tests_criterion() -> None:
    assert score_project("pytest suite included.").criteria["has_tests"] is True
    assert score_project("no validation at all.").criteria["has_tests"] is False


@pytest.mark.unit
def test_score_project_has_cloud_criterion() -> None:
    assert score_project("deployed to azure.").criteria["has_cloud"] is True
    assert score_project("runs locally only.").criteria["has_cloud"] is False


@pytest.mark.unit
def test_score_project_has_ai_ml_criterion() -> None:
    assert score_project("llm-powered rag pipeline.").criteria["has_ai_ml"] is True
    assert score_project("static file server.").criteria["has_ai_ml"] is False


@pytest.mark.unit
def test_score_project_has_docker_criterion() -> None:
    assert score_project("docker container.").criteria["has_docker"] is True
    assert score_project("no containerization.").criteria["has_docker"] is False


@pytest.mark.unit
def test_score_project_score_is_rounded() -> None:
    result = score_project("api only")
    assert result.score == round(result.score, 2)


@pytest.mark.unit
def test_suggest_readme_sections_api() -> None:
    sections = suggest_readme_sections("api")
    assert "API examples" in sections
    assert "Docker" in sections
    assert "Deployment" in sections
    assert "What this proves" in sections


@pytest.mark.unit
def test_suggest_readme_sections_ml() -> None:
    sections = suggest_readme_sections("ml")
    assert "Training" in sections
    assert "Evaluation" in sections
    assert "Metrics" in sections


@pytest.mark.unit
def test_suggest_readme_sections_rag() -> None:
    sections = suggest_readme_sections("rag")
    assert "Corpus" in sections
    assert "Retrieval strategy" in sections


@pytest.mark.unit
def test_suggest_readme_sections_agent() -> None:
    sections = suggest_readme_sections("agent")
    assert "Graph" in sections
    assert "State transitions" in sections
    assert "Tool schemas" in sections


@pytest.mark.unit
def test_suggest_readme_sections_unknown_type() -> None:
    sections = suggest_readme_sections("unknown-type")
    expected = ["What this proves", "Scope", "Architecture", "Run locally", "Test", "Tradeoffs"]
    assert sections == expected


@pytest.mark.unit
def test_suggest_readme_sections_case_insensitive() -> None:
    assert suggest_readme_sections("API") == suggest_readme_sections("api")


@pytest.mark.unit
def test_suggest_readme_sections_base_always_present() -> None:
    base = ["What this proves", "Scope", "Architecture", "Run locally", "Test", "Tradeoffs"]
    for project_type in ("api", "ml", "rag", "agent", "other"):
        sections = suggest_readme_sections(project_type)
        for item in base:
            assert item in sections


@pytest.mark.unit
def test_generate_portfolio_summary_count() -> None:
    summary = generate_portfolio_summary(["lab1", "lab2", "lab3"])
    assert "3" in summary


@pytest.mark.unit
def test_generate_portfolio_summary_single() -> None:
    summary = generate_portfolio_summary(["lab1"])
    assert "1" in summary


@pytest.mark.unit
def test_generate_portfolio_summary_empty() -> None:
    summary = generate_portfolio_summary([])
    assert "0" in summary


@pytest.mark.unit
def test_generate_portfolio_summary_is_string() -> None:
    result = generate_portfolio_summary(["a", "b"])
    assert isinstance(result, str)
    assert len(result) > 0
