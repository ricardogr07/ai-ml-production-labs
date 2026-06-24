# Lab 05: Ollama Local LLM API

## What this proves

A production-grade FastAPI wrapper around a locally running open-weight LLM via Ollama. The service
adds structured logging, Pydantic validation, health endpoint, and clean HTTP error translation over
the raw Ollama `/api/generate` call, proving that local inference can be served behind a stable,
testable API boundary without any cloud LLM dependency.

## Scope

- Endpoint: `POST /summarize` backed by a configurable local Ollama model
- Input: `{ "text": "...", "model": "phi3.5", "max_tokens": 256 }`
- Output: `{ "summary": "...", "model": "...", "latency_ms": ... }`
- Deployment targets: local process, Docker Compose (with bundled Ollama service), Azure Container Apps
- Non-goals: streaming responses, model management, multi-model parallelism

## Architecture

See [docs/architecture.md](docs/architecture.md) for full Mermaid diagrams.

```
Client
  POST /summarize
    FastAPI (app.py)
      SummarizeService (service.py)
        OllamaClient (ollama_client.py)
          Ollama daemon  http://localhost:11434
```

## Tech stack

| Component | Library | Why |
|-----------|---------|-----|
| HTTP framework | FastAPI 0.115 | async-native, auto OpenAPI docs |
| HTTP client | httpx (async) | non-blocking Ollama calls |
| Validation | Pydantic v2 | boundary enforcement, 422 on bad input |
| Settings | pydantic-settings | env var binding for OLLAMA_BASE_URL etc. |
| Logging | structlog (shared) | structured JSON output |
| LLM runtime | Ollama 0.30 | local CPU inference, no API key |

## Prerequisites

```bash
# Install Ollama from https://ollama.com/download, then:
ollama pull phi3.5       # 2.2 GB, primary model (CPU-friendly)
ollama pull tinyllama    # 637 MB, lightweight alternative
ollama serve             # start daemon (or it auto-starts on first call)
```

## Run locally

```bash
uv sync --all-packages
uv run --package ollama-local-llm-api uvicorn ollama_local_llm_api.app:app --reload
```

## Test

```bash
# All markers (unit + integration, no Ollama required)
uv run tox -e py312

# Unit only
uv run pytest labs/05-ollama-local-llm-api/tests/unit -v

# Integration only
uv run pytest labs/05-ollama-local-llm-api/tests/integration -v
```

## API examples

```bash
# Health check (no Ollama required)
curl http://localhost:8000/health

# Summarize with default model (phi3.5)
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "FastAPI is a modern Python web framework built on Starlette and Pydantic v2."}'

# Summarize with tinyllama for faster response
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Containers package an app and its dependencies into a portable unit.", "model": "tinyllama", "max_tokens": 64}'
```

Example response:

```json
{
  "summary": "FastAPI is a fast, async Python framework for building APIs with automatic validation and documentation.",
  "model": "phi3.5",
  "latency_ms": 4231.7
}
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama daemon URL |
| `OLLAMA_DEFAULT_MODEL` | `phi3.5` | Model used when request omits `model` |
| `OLLAMA_TIMEOUT_SECONDS` | `60.0` | Per-request timeout |
| `LOG_LEVEL` | `INFO` | structlog level |
| `ENVIRONMENT` | `local` | Runtime environment label |

## Production notes

- `/health` never calls Ollama and will always return 200 while the FastAPI process is alive.
  Use it as the Container Apps liveness probe.
- A 503 response means the Ollama daemon is unreachable (`OLLAMA_BASE_URL` misconfigured or Ollama
  not running). A 504 means Ollama is alive but the model took longer than `OLLAMA_TIMEOUT_SECONDS`.
- `phi3.5` runs on CPU without a GPU. Expect 3-8 seconds per summary on a typical dev machine.
  Use `tinyllama` if latency is a concern during local testing.

## Tradeoffs

- Ollama must be running and a model must be pulled before `/summarize` works. The `/health`
  endpoint is always available and does not probe Ollama.
- No model warm-up: first inference after a cold Ollama start loads the model into RAM, adding 1-3s.
- `OLLAMA_TIMEOUT_SECONDS` defaults to 60s. Tune this down for interactive use or up for large
  `max_tokens` values with slower models.
- Tests mock `OllamaClient` and do not require a running Ollama instance.
