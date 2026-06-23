# Architecture: FastMCP Portfolio Tools

## Overview

Lab 03 is a stateless MCP (Model Context Protocol) server built with FastMCP. It exposes three deterministic, rule-based tools that an MCP client (Claude Desktop, Cline, or any compatible host) can call to analyze and document software projects.

## Technology choices

| Concern | Choice | Why |
|---|---|---|
| Protocol | MCP (Model Context Protocol) | Standard interface for LLM tool use |
| Framework | FastMCP 3.x | Decorator-based server with automatic schema generation |
| Transport | stdio (default) / streamable-http (Docker) | stdio for direct LLM integration; HTTP for container-based use |
| Validation | Pydantic v2 | Typed tool responses; FastMCP generates MCP input/output schemas automatically |
| Logging | structlog (via shared) | Structured JSON output consistent with other labs |

## Component diagram

```mermaid
graph TD
    Client["MCP Client<br/>(Claude, Cline, etc.)"]
    Server["FastMCP Server<br/>portfolio-tools"]
    Dispatcher["Tool Dispatcher"]
    T1["score_project<br/>returns ProjectScore"]
    T2["suggest_readme_sections<br/>returns list[str]"]
    T3["generate_portfolio_summary<br/>returns str"]

    Client -->|tool call / MCP protocol| Server
    Server --> Dispatcher
    Dispatcher --> T1
    Dispatcher --> T2
    Dispatcher --> T3
    T1 -->|ProjectScore JSON| Client
    T2 -->|sections list| Client
    T3 -->|summary string| Client
```

## Request flow

```mermaid
sequenceDiagram
    participant C as MCP Client
    participant S as FastMCP Server
    participant T as Tool handler

    C->>S: tools/list
    S-->>C: [score_project, suggest_readme_sections, generate_portfolio_summary]

    C->>S: tools/call score_project {project_description: "..."}
    S->>T: score_project("...")
    T-->>S: ProjectScore(score=0.8, criteria={...}, recommendation="strong")
    S-->>C: CallToolResult (JSON-serialized ProjectScore)
```

## Tool schemas

### `score_project`

Input: `project_description: str`

Output: `ProjectScore`

```json
{
  "score": 0.8,
  "criteria": {
    "has_api": true,
    "has_tests": true,
    "has_cloud": false,
    "has_ai_ml": true,
    "has_docker": true
  },
  "recommendation": "strong"
}
```

Score is the fraction of criteria matched (0.0 to 1.0). Recommendation is "strong" at >= 0.6.

### `suggest_readme_sections`

Input: `project_type: str` (one of: `api`, `ml`, `rag`, `agent`, or any unknown value)

Output: `list[str]` - base sections plus type-specific additions.

### `generate_portfolio_summary`

Input: `projects: list[str]`

Output: `str` - one-paragraph summary stating the project count and portfolio scope.

## Non-goals

- No persistence: all tool results are stateless and deterministic.
- No LLM calls inside tools: logic is keyword-based to keep the focus on MCP transport and schema design, not model behavior.
- No cloud infrastructure: the server runs locally or in Docker, never deployed to Azure.
