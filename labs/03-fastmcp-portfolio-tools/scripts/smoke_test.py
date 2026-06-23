#!/usr/bin/env python
"""Smoke test: invoke all three portfolio tools via in-process FastMCP Client."""

from __future__ import annotations

import asyncio
import sys

from fastmcp import Client
from fastmcp_portfolio_tools.server import mcp


async def main() -> None:
    async with Client(mcp) as c:
        r1 = await c.call_tool(
            "score_project",
            {"project_description": "FastAPI ML service with pytest, Azure, and Docker."},
        )
        assert not r1.is_error, f"score_project failed: {r1}"
        assert r1.structured_content is not None
        score = r1.structured_content["score"]
        assert isinstance(score, float), f"expected float score, got {type(score)}"
        print(f"score_project OK: score={score}")

        r2 = await c.call_tool("suggest_readme_sections", {"project_type": "api"})
        assert not r2.is_error, f"suggest_readme_sections failed: {r2}"
        assert r2.structured_content is not None
        sections = r2.structured_content["result"]
        assert "What this proves" in sections, "base section missing"
        assert "API examples" in sections, "api-specific section missing"
        print(f"suggest_readme_sections OK: {len(sections)} sections")

        r3 = await c.call_tool("generate_portfolio_summary", {"projects": ["lab1", "lab2", "lab3"]})
        assert not r3.is_error, f"generate_portfolio_summary failed: {r3}"
        assert r3.structured_content is not None
        summary = r3.structured_content["result"]
        assert "3" in summary, "project count missing from summary"
        print(f"generate_portfolio_summary OK: {len(summary)} chars")

    print("All tools OK.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
