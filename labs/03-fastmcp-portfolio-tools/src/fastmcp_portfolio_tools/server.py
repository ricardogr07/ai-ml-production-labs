"""FastMCP server with portfolio analysis tools."""

from __future__ import annotations

from typing import Literal

from fastmcp import FastMCP

from fastmcp_portfolio_tools.config import Settings
from fastmcp_portfolio_tools.schemas import ProjectScore
from production_labs_shared.logging import configure_logging

_settings = Settings()
configure_logging(_settings.log_level)

mcp = FastMCP("portfolio-tools")


@mcp.tool()
def score_project(project_description: str) -> ProjectScore:
    """Score a project description against the portfolio thesis criteria."""
    desc = project_description.lower()
    criteria = {
        "has_api": any(kw in desc for kw in ("api", "fastapi", "endpoint")),
        "has_tests": any(kw in desc for kw in ("test", "pytest", "unit")),
        "has_cloud": any(kw in desc for kw in ("azure", "aws", "gcp", "cloud")),
        "has_ai_ml": any(kw in desc for kw in ("ml", "ai", "model", "llm", "rag")),
        "has_docker": "docker" in desc,
    }
    score = sum(criteria.values()) / len(criteria)
    recommendation: Literal["strong", "needs work"] = "strong" if score >= 0.6 else "needs work"
    return ProjectScore(score=round(score, 2), criteria=criteria, recommendation=recommendation)


@mcp.tool()
def suggest_readme_sections(project_type: str) -> list[str]:
    """Suggest README sections for a given project type."""
    base = ["What this proves", "Scope", "Architecture", "Run locally", "Test", "Tradeoffs"]
    additions: dict[str, list[str]] = {
        "api": ["API examples", "Docker", "Deployment"],
        "ml": ["Training", "Evaluation", "Metrics"],
        "rag": ["Corpus", "Retrieval strategy", "Evaluation"],
        "agent": ["Graph", "State transitions", "Tool schemas"],
    }
    extra = additions.get(project_type.lower(), [])
    return base + extra


@mcp.tool()
def generate_portfolio_summary(projects: list[str]) -> str:
    """Generate a one-paragraph portfolio summary from a list of project descriptions."""
    count = len(projects)
    return (
        f"Portfolio of {count} production-shaped AI/ML micro-labs demonstrating "
        "full-stack engineering from containerized APIs to RAG systems and agent workflows."
    )
