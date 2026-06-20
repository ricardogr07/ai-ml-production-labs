# Lab 08: LangGraph Project Agent

## What this proves

A controlled agentic workflow using LangGraph's state graph. Each node in the graph performs a deterministic transformation on typed `ProjectState`, demonstrating how to build agents as explicit workflows rather than black-box LLM chains.

## Scope

- Capability: Analyze a project idea through a typed state graph
- Input: `{ "project_idea": "..." }`
- Output: `{ project_type, thesis_score, missing_artifacts, implementation_plan, recommendation }`
- Deployment target: local (callable as library or CLI)
- Non-goals: LLM-generated nodes (scaffold uses deterministic logic; swap in real LLM calls per node)

## Architecture

```text
project_idea
  → classify_project_type
  → score_against_portfolio_thesis
  → identify_missing_artifacts
  → generate_implementation_plan
  → return_scorecard
```

## Run locally

```bash
uv sync
uv run --package langgraph-project-agent python -c "
from langgraph_project_agent.graph import compiled_graph
from langgraph_project_agent.state import ProjectState
result = compiled_graph.invoke(ProjectState(project_idea='A RAG service with FastAPI, tests, Docker, and Azure.'))
print(result['scorecard'])
"
```

## Test

```bash
uv run --package langgraph-project-agent pytest labs/08-langgraph-project-agent/tests
```

## Tradeoffs

- Deterministic node logic makes the graph fully testable without LLM API calls.
- Replace node functions with real LLM calls (via `langchain-anthropic`) for production use.
- No tool calls in the scaffold; add `@tool` decorated functions bound to nodes for real agentic capability.
