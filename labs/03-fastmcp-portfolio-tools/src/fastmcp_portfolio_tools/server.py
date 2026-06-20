"""FastMCP server with portfolio analysis tools."""

from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("portfolio-tools")


@mcp.tool()
def score_project(project_description: str) -> dict[str, object]:
    """Score a project description against the portfolio thesis criteria."""
    criteria = {
        "has_api": any(kw in project_description.lower() for kw in ("api", "fastapi", "endpoint")),
        "has_tests": any(kw in project_description.lower() for kw in ("test", "pytest", "unit")),
        "has_cloud": any(kw in project_description.lower() for kw in ("azure", "aws", "gcp", "cloud")),
        "has_ai_ml": any(kw in project_description.lower() for kw in ("ml", "ai", "model", "llm", "rag")),
        "has_docker": "docker" in project_description.lower(),
    }
    score = sum(criteria.values()) / len(criteria)
    return {"score": round(score, 2), "criteria": criteria, "recommendation": "strong" if score >= 0.6 else "needs work"}


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
