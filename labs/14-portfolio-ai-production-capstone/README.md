# Lab 14: Portfolio AI Production Capstone

## What this proves

The capstone integrates the best pieces from all prior labs into one coherent production-shaped AI service: a FastAPI API with OpenTelemetry instrumentation, a LangGraph agent for project analysis, Cosmos DB for persistence, and Azure Container Apps deployment, all from a single Dockerfile.

## Scope

- Capability: Analyze a project idea through a LangGraph agent with RAG memory and OTel observability
- Input: `{ "project_idea": "..." }`
- Output: `{ project_type, thesis_score, missing_artifacts, implementation_plan, recommendation }`
- Deployment target: Azure Container Apps + Application Insights
- Non-goals: UI, authentication, streaming

## Architecture

```text
client → FastAPI (OTel) → LangGraph agent
                               ├── Cosmos DB (RAG memory of past analyses)
                               ├── Anthropic Claude (node LLM calls)
                               └── portfolio thesis rules
                          → AnalyzeResponse
                               ↓
                          Azure Container Apps + Application Insights
```

## Components from prior labs

| Component | Source lab |
|---|---|
| FastAPI skeleton | Lab 01 |
| OpenTelemetry | Lab 13 |
| LangGraph agent | Lab 08 |
| Cosmos DB repository | Lab 04 |
| Shared logging + health | shared/ |

## Run locally

```bash
uv sync
uv run --package portfolio-ai-production-capstone uvicorn portfolio_ai_production_capstone.app:app --reload
```

## Test

```bash
uv run --package portfolio-ai-production-capstone pytest labs/14-portfolio-ai-production-capstone/tests
```

## Docker

```bash
docker build -f labs/14-portfolio-ai-production-capstone/Dockerfile -t portfolio-ai-production-capstone:local .
docker run --rm -p 8000:8000 --env-file labs/14-portfolio-ai-production-capstone/.env.example portfolio-ai-production-capstone:local
```

## Tradeoffs

- Deterministic agent nodes in the scaffold; replace with real LLM calls using `langchain-anthropic`.
- Cosmos DB persistence is optional locally; `InMemoryEvalStoreRepository` from Lab 04 is the fallback.
- This is not a "demo kitchen sink." Each component is independently testable and sourced from a completed lab.
