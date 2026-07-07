# Lab 08: LangGraph Project Agent

## What this proves

A controlled agentic workflow using LangGraph's state graph. Each node performs a typed transformation on `ProjectState`, demonstrating how to build agents as explicit workflows rather than black-box LLM chains. The same graph runs at three complexity tiers, selected by one environment variable: deterministic heuristics (no LLM), a local or dockerized Ollama model, or the Anthropic API.

## Scope

- Capability: Analyze a project idea through a typed state graph
- Input: `{ "project_idea": "..." }`
- Output: `{ project_type, thesis_score, missing_artifacts, implementation_plan, recommendation }`
- Deployment target: local (callable as library or CLI)
- Non-goals: tool-calling agents (nodes are single structured-output LLM calls, not tool loops)

## Architecture

```text
project_idea
  → classify_project_type
  → score_against_portfolio_thesis
  → identify_missing_artifacts
  → generate_implementation_plan
  → return_scorecard
```

The first four nodes dispatch on `LLM_PROVIDER`: with `none` they run keyword heuristics; with `ollama` or `anthropic` they call the model through one shared code path (`ChatOllama` / `ChatAnthropic` with `.with_structured_output(...)`, so responses are validated Pydantic objects). `return_scorecard` is always deterministic assembly.

## Provider tiers

| `LLM_PROVIDER` | What runs | Needs |
|---|---|---|
| `none` (default) | Deterministic heuristics | Nothing |
| `ollama` | Local Ollama model (default `llama3.2`) | Ollama on `localhost:11434` (host install or docker-compose) |
| `anthropic` | Anthropic API (default `claude-opus-4-8`) | `ANTHROPIC_API_KEY` |

Configuration lives in `.env` (see `.env.example`): `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`.

## Run locally

Tier 1, deterministic (no services, doubles as the smoke test):

```bash
uv sync --all-packages
uv run python -m langgraph_project_agent "A RAG service with FastAPI, tests, Docker, and Azure."
```

Tier 2, Ollama (dockerized; skip the compose steps if Ollama already runs on the host):

```bash
docker compose -f labs/08-langgraph-project-agent/docker-compose.yml up -d
docker compose -f labs/08-langgraph-project-agent/docker-compose.yml exec ollama ollama pull llama3.2
LLM_PROVIDER=ollama uv run python -m langgraph_project_agent "A RAG service with FastAPI, tests, Docker, and Azure."
```

Tier 3, Anthropic API:

```bash
ANTHROPIC_API_KEY=sk-ant-... LLM_PROVIDER=anthropic uv run python -m langgraph_project_agent "A RAG service with FastAPI, tests, Docker, and Azure."
```

On PowerShell, set variables with `$env:LLM_PROVIDER = "ollama"` before the `uv run` command.

## Test

```bash
# Unit tests: hermetic, provider none
uv run pytest labs/08-langgraph-project-agent -m unit

# Integration: requires a reachable Ollama with the model pulled, otherwise skips
uv run pytest labs/08-langgraph-project-agent -m integration

# End to end: requires ANTHROPIC_API_KEY, otherwise skips
uv run pytest labs/08-langgraph-project-agent -m e2e
```

## Pipeline and Azure infra

Three CI surfaces exercise the tiers:

- Every PR (`ci.yml`): unit tests run inside the tox gates, the lab Dockerfile is built, and the `anthropic-e2e` job runs the lab e2e suite against the Anthropic API using the `ANTHROPIC_API_KEY` repository secret (skips when the secret is unavailable, e.g. fork PRs).
- Manual dispatch (`integration-test.yml`, lab `08-langgraph-project-agent`, image name `langgraph-project-agent`): builds and pushes the agent image to GHCR, then `terraform apply` on `infra/main.tf` deploys two Azure Container Instances:
  - a one-shot agent container running `LLM_PROVIDER=anthropic` with the API key injected as a secure environment variable; CI waits for it to terminate, pulls the logs, and asserts the scorecard is present with exit code 0
  - an Ollama server with a public endpoint; CI pulls `llama3.2` through its API and runs this lab's integration tests against it
  - teardown always destroys both container groups, including after failed deploys
- The Ollama endpoint is public and unauthenticated for the minutes the run lasts; it is destroyed at the end of every run.

## Tradeoffs

- Deterministic tier keeps the graph fully testable without LLM calls; unit tests never touch the network.
- One structured-output code path serves both LLM providers, so adding a provider is a new branch in `llm.get_chat_model()` only.
- Small Ollama models can be flaky with JSON structured output; `OLLAMA_MODEL` is overridable if `llama3.2` misbehaves.
- No tool calls; add `@tool` decorated functions bound to nodes for real agentic capability.
