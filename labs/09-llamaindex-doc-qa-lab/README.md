# Lab 09: LlamaIndex Doc Q&A

## What this proves

A containerized retrieval-augmented generation service using LlamaIndex: a Wikipedia corpus is chunked, embedded, and indexed in Qdrant, then queried through a LlamaIndex query engine that retrieves the top-k most relevant chunks and synthesizes a cited answer with an LLM. Generation defaults to a local Ollama model, with the Anthropic API as an optional second tier. Unlike labs 06 and 07 (which only store or retrieve vectors), this lab does the full retrieve-and-generate loop.

## Scope

- Capability: Answer natural-language questions over a Wikipedia corpus with cited source chunks
- Input: `{ "question": "...", "top_k": 3 }`
- Output: `{ "answer": "...", "sources": [{ "content", "source", "score" }] }`
- Deployment target: containerized (Docker Compose locally, Azure Container Apps + Container Instances)
- Non-goals: multi-turn conversation, hybrid/sparse search, corpus updates via the API (ingestion is a separate script)

## Architecture

```text
data/wikipedia_corpus.json → scripts/seed_data.py → chunk + embed (HuggingFace) → Qdrant collection
POST /query {question, top_k} → VectorStoreIndex.from_vector_store(Qdrant) → query engine
  (similarity_top_k = top_k, llm = Ollama | Anthropic) → answer + source chunks
```

Three containers: `app` (FastAPI + LlamaIndex) depends on `ollama` (generation) and `qdrant` (retrieval). Embeddings always run locally via `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim), regardless of which LLM provider is generating the answer — Anthropic has no embeddings API, so embedding can never be provider-dependent.

## Provider tiers

| `LLM_PROVIDER` | What runs | Needs |
|---|---|---|
| `ollama` (default) | Local Ollama model (default `llama3.2`) | Ollama on `localhost:11434` (host install or docker-compose) |
| `anthropic` | Anthropic API (default `claude-opus-4-8`) | `ANTHROPIC_API_KEY` |

Configuration lives in `.env` (see `.env.example`): `LLM_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `QDRANT_URL`, `QDRANT_COLLECTION`, `EMBEDDING_MODEL_NAME`.

## Run locally

```bash
docker compose -f labs/09-llamaindex-doc-qa-lab/docker-compose.yml up -d --build

# Ollama tier only: pull the generation model into the container (first run; the
# ollama_data volume caches it afterwards). Not needed for the Anthropic tier.
docker compose -f labs/09-llamaindex-doc-qa-lab/docker-compose.yml exec ollama ollama pull llama3.2

uv run --frozen --package llamaindex-doc-qa-lab python labs/09-llamaindex-doc-qa-lab/scripts/seed_data.py

curl localhost:8000/health
curl -X POST localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is DNA?", "top_k": 3}'
```

The Ollama tier is the default and needs no `.env`. To use the Anthropic tier instead, `cp labs/09-llamaindex-doc-qa-lab/.env.example labs/09-llamaindex-doc-qa-lab/.env`, set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in that `.env`, then `docker compose up` (Compose loads `.env` when present). For a host-run `uvicorn llamaindex_doc_qa_lab.app:app`, export the same variables instead.

## Test

```bash
# Unit tests: hermetic, no network
uv run pytest labs/09-llamaindex-doc-qa-lab -m unit

# Integration: TestClient tests always run; the real-Ollama query test requires a
# reachable Ollama with the model pulled and a seeded Qdrant, otherwise it skips
uv run pytest labs/09-llamaindex-doc-qa-lab -m integration

# End to end: requires ANTHROPIC_API_KEY and a seeded Qdrant, otherwise skips
uv run pytest labs/09-llamaindex-doc-qa-lab -m e2e
```

## Pipeline and Azure infra

Two CI surfaces exercise this lab:

- Every PR (`ci.yml`): unit and mocked-integration tests run inside the tox gates, the lab Dockerfile is built, and the `anthropic-e2e` job runs this lab's (and lab 08's) e2e suite against the Anthropic API using the `ANTHROPIC_API_KEY` repository secret (skips when the secret is unavailable, e.g. fork PRs).
- Manual dispatch (`integration-test.yml`, lab `09-llamaindex-doc-qa-lab`, image name `llamaindex-doc-qa-lab`): builds and pushes the app image to GHCR, then `terraform apply` on `infra/main.tf` deploys three resources:
  - the app on Azure Container Apps (scale-to-zero, `min_replicas = 0`)
  - a public Ollama server on Azure Container Instances (same shape as lab 08's)
  - a public Qdrant server on Azure Container Instances
  - CI waits for Ollama and Qdrant to become reachable, pulls `llama3.2`, seeds the corpus into the deployed Qdrant, then runs the HTTP smoke test against the deployed app
  - teardown always destroys all three resources, including after failed deploys

The Ollama and Qdrant endpoints are public and unauthenticated for the minutes the run lasts, destroyed at the end of every run. Qdrant is additionally *writable* during that window (`seed_data.py` upserts into it) — see Production notes.

## Production notes

- Qdrant would run with `QDRANT__SERVICE__API_KEY` set and/or behind private networking; the public, unauthenticated ACI here exists only to keep the lab's CI loop self-contained and short-lived.
- The Docker image pre-warms the `sentence-transformers` embedding model cache at build time so `min_replicas = 0` cold starts don't pay a ~90MB download before the first query.
- `scripts/seed_data.py` is not idempotent-by-default; pass `--recreate` to drop and rebuild the collection rather than risk duplicate points on a re-run.

## Tradeoffs

- Embeddings are always local (`sentence-transformers`), decoupling retrieval quality from which LLM provider is generating — but it also means embedding quality can't be upgraded by switching providers.
- Qdrant and Ollama are both required for every code path except the mocked `TestClient` tests; there's no in-memory fallback vector store.
- `top_k` is the only retrieval knob exposed; no reranking or query expansion (see lab 07 for those strategies).
