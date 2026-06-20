from __future__ import annotations

import pytest

from fastmcp_portfolio_tools.server import score_project, suggest_readme_sections, generate_portfolio_summary


@pytest.mark.unit
def test_score_project_high_score() -> None:
    result = score_project("FastAPI ML service with pytest, Azure deployment, and Docker.")
    assert result["score"] >= 0.6
    assert result["recommendation"] == "strong"


@pytest.mark.unit
def test_score_project_low_score() -> None:
    result = score_project("A simple script.")
    assert result["score"] < 0.6


@pytest.mark.unit
def test_suggest_readme_sections_api() -> None:
    sections = suggest_readme_sections("api")
    assert "API examples" in sections
    assert "What this proves" in sections


@pytest.mark.unit
def test_generate_portfolio_summary() -> None:
    summary = generate_portfolio_summary(["lab1", "lab2", "lab3"])
    assert "3" in summary
