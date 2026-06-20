# Lab 03: FastMCP Portfolio Tools

## What this proves

An MCP server exposing typed, deterministic tools for portfolio project analysis. Tools have typed schemas, are testable in isolation, and run locally as an MCP-compatible server, demonstrating how to expose structured capability to an LLM runtime rather than relying on freeform generation.

## Scope

- Capability: MCP server with portfolio analysis tools
- Input: tool calls from an MCP client (Claude, Cline, etc.)
- Output: typed tool responses
- Deployment target: local (stdio or HTTP transport)
- Non-goals: LLM-generated content, UI, persistence

## Architecture

```text
MCP client → FastMCP server → tool dispatcher
              ├── score_project(description)
              ├── suggest_readme_sections(project_type)
              └── generate_portfolio_summary(projects)
```

## Run locally

```bash
uv sync
uv run --package fastmcp-portfolio-tools fastmcp run labs/03-fastmcp-portfolio-tools/src/fastmcp_portfolio_tools/server.py
```

## Test

```bash
uv run --package fastmcp-portfolio-tools pytest labs/03-fastmcp-portfolio-tools/tests
```

## Tradeoffs

- Tools use deterministic rule-based logic to keep the lab focused on the MCP transport and schema, not LLM behavior.
- No persistence: tool results are stateless.
