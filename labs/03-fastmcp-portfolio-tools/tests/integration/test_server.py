"""Integration tests using FastMCP Client with in-process transport."""

from __future__ import annotations

import pytest
from fastmcp import Client
from fastmcp_portfolio_tools.server import mcp


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_tools_registered() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {t.name for t in tools}
        assert {"score_project", "suggest_readme_sections", "generate_portfolio_summary"} <= names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_score_project_via_client() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "score_project",
            {"project_description": "FastAPI service with pytest and Azure Docker."},
        )
    assert not result.is_error
    assert result.structured_content is not None
    data = result.structured_content
    assert isinstance(data["score"], float)
    assert data["score"] >= 0.6
    assert data["recommendation"] == "strong"
    assert isinstance(data["criteria"], dict)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_suggest_readme_sections_via_client() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "suggest_readme_sections",
            {"project_type": "api"},
        )
    assert not result.is_error
    assert result.structured_content is not None
    sections: list[str] = result.structured_content["result"]
    assert "What this proves" in sections
    assert "API examples" in sections


@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_portfolio_summary_via_client() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "generate_portfolio_summary",
            {"projects": ["lab1", "lab2", "lab3"]},
        )
    assert not result.is_error
    assert result.structured_content is not None
    summary: str = result.structured_content["result"]
    assert "3" in summary
    assert len(summary) > 0
