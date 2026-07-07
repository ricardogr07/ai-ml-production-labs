# Lab 07: RAG Retrieval Strategy Lab

## What this proves

Retrieval quality is mostly a retrieval problem, not a prompt problem. This lab compares four retrieval strategies over a real corpus (25 Wikipedia article extracts across 5 categories) and a hand-curated golden query set, computing Recall@3, MRR, latency, and token count to show which strategy actually performs better, and that "more sophisticated" doesn't always mean "better."

## Scope

- Capability: Compare retrieval strategies with reproducible metrics
- Input: text corpus, golden query set with relevant document IDs
- Output: metrics table (Recall@3, MRR, latency_ms, token_count per strategy)
- Deployment target: local (Qdrant via Docker, no cloud dependency)
- Non-goals: generation, a full RAG pipeline, a UI

## Architecture

See [docs/architecture.md](docs/architecture.md) for component and sequence diagrams.

```text
corpus -> SentenceTransformer -> QdrantVectorStoreRepository.add()
golden queries -> [naive | metadata-filtered | reranked | query-expanded] retrieval
                                  |
                    Recall@3 / MRR / latency_ms / token_count table
```

## Strategies

| Strategy | Description |
|---|---|
| Naive | Brute-force cosine similarity over all documents (via Qdrant) |
| Metadata-filtered | Pre-filter by category via Qdrant's payload filter, then similarity |
| Reranked | Similarity search for top 10 candidates -> cross-encoder rerank |
| Query-expanded | Expand query with a local synonym dictionary, then similarity |

Chunk-size comparison and LLM-based query expansion (both listed in the
original project blueprint) are explicitly out of scope: the former is an
experiment-design variant rather than a new retrieval algorithm, and the
latter would need a cloud LLM call, which conflicts with this lab's "no
cloud dependency" scope. Four strategies comfortably clears the "at least
three" bar.

## Prerequisites

- Docker (for the local Qdrant instance)
- Python 3.12 via `uv`

The `all-MiniLM-L6-v2` embedding model and `cross-encoder/ms-marco-MiniLM-L-6-v2`
reranker (~90 MB and ~90 MB) download automatically on first run.

## Run locally

```bash
# Start Qdrant (port 6333)
docker compose up -d

# Run the strategy comparison
uv run python labs/07-rag-retrieval-strategy-lab/scripts/run_comparison.py
```

The corpus (`data/wikipedia_corpus.json`) is 25 real Wikipedia article
extracts across 5 categories (machine learning, cooking, history, sports,
astronomy), content from Wikipedia,
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). To refresh
it, run `scripts/fetch_wikipedia_corpus.py` (one-off, stdlib only, not part
of any test or CI path). The golden query set
(`data/golden_queries.json`) is hand-curated against this corpus.

## Test

```bash
# Unit tests (no Qdrant required, uses embedded :memory: mode)
uv run pytest labs/07-rag-retrieval-strategy-lab/tests/unit -m unit

# Integration tests (requires: docker compose up -d; downloads real models)
uv run pytest labs/07-rag-retrieval-strategy-lab/tests/integration -m integration

# All tests via tox
tox -e py312
```

## Results

```text
strategy              recall@3       mrr    latency_ms    tokens
naive                    1.000     1.000         12.81     224.2
metadata_filtered        1.000     1.000         11.43     224.2
reranked                 0.917     1.000        324.46     243.2
expanded_query           1.000     1.000         29.42     225.4
```

Naive cosine similarity already gets perfect Recall@3/MRR on this corpus:
5 clearly distinct categories and straightforward queries give the
embedding model an easy job, so there's a ceiling effect that
metadata-filtering and query-expansion don't have room to improve on (they
match naive exactly here). The interesting result is **reranking made
things slightly worse** (0.917 vs 1.000 recall) while being roughly 25x
slower (324ms vs 13ms) — the cross-encoder's training distribution (MS
MARCO passage ranking) doesn't perfectly match short Wikipedia extracts,
and reordering an already-good candidate set has more room to hurt than
help. This is the actual point of the lab: a fancier technique isn't free,
and it doesn't help when the simpler baseline is already good enough.
Metadata-filtering's edge case is when a query's category is ambiguous or
wrong; reranking's and query-expansion's costs (latency, token count) are
worth paying only when naive search demonstrably struggles.

## Tradeoffs

- 25-document corpus across 5 categories keeps the lab reproducible without a large real dataset, while still being large enough for metadata filtering and reranking to have a real effect.
- Embeddings and reranking run locally via `sentence-transformers`, no API key needed.
- Query expansion uses a small local synonym dictionary rather than an LLM call, to keep the lab's "no cloud dependency" scope honest, at the cost of only covering vocabulary the dictionary knows about.
- Qdrant runs via Docker locally (not embedded `:memory:` mode) for `run_comparison.py` and integration tests, so the comparison exercises the same client/server path a real deployment would use; unit tests use `:memory:` mode to stay fast.
