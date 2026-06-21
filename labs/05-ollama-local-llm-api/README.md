# Lab 05: Ollama Local LLM API

## What this proves

A FastAPI wrapper around a locally-running open-model LLM via Ollama. The service handles provider failures, timeout handling, and latency measurement, demonstrating a clean API boundary over local inference without OpenAI dependency.

## Scope

- Capability: `/summarize` endpoint backed by a local Ollama LLM
- Input: `{ "text": "...", "model": "llama3.2", "max_tokens": 256 }`
- Output: `{ "summary": "...", "model": "...", "latency_ms": ... }`
- Deployment target: local (Ollama required), Dockerfile for Azure Container Apps
- Non-goals: streaming responses, model management, multiple concurrent models

## Architecture

```text
client → FastAPI /summarize → OllamaClient → local Ollama (http://localhost:11434)
                                                   ↓
                                          structured response + latency
```

## Prerequisites

```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3.2
ollama serve
```

## Run locally

```bash
uv sync
uv run --package ollama-local-llm-api uvicorn ollama_local_llm_api.app:app --reload
```

## Test

```bash
uv run --package ollama-local-llm-api pytest labs/05-ollama-local-llm-api/tests
```

## Tradeoffs

- Local-only by default: Ollama must be running for `/summarize` to work, but tests mock the client.
- No model caching or warm-up: first request incurs model load latency.
- Timeout is fixed at 30s; production would tune per-model.
