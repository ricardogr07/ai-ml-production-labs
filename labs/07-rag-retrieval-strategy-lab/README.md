# Lab 07: RAG Retrieval Strategy Lab

## What this proves

Retrieval quality is mostly a retrieval problem, not a prompt problem. This lab compares multiple retrieval strategies over a fixed corpus and golden query set, computing Recall@3 and MRR to show which strategy actually performs better and why.

## Scope

- Capability: Compare retrieval strategies with reproducible metrics
- Input: text corpus, golden query set with relevant document IDs
- Output: metrics table (Recall@3, MRR, latency_ms per strategy)
- Deployment target: local (no cloud dependency)
- Non-goals: generation, a full RAG pipeline, a UI

## Architecture

```text
corpus → embeddings → vector store
golden queries → [naive | metadata-filtered | reranked | query-expanded] retrieval
                                  ↓
                    Recall@3 / MRR / latency table
```

## Strategies

| Strategy | Description |
|---|---|
| Naive | Brute-force cosine similarity over all documents |
| Metadata-filtered | Pre-filter by metadata field, then similarity |
| Reranked | Similarity search → cross-encoder rerank |
| Query-expanded | Expand query with synonyms, then similarity |

## Run locally

```bash
uv sync
uv run --package rag-retrieval-strategy-lab python labs/07-rag-retrieval-strategy-lab/scripts/run_comparison.py
```

## Test

```bash
uv run --package rag-retrieval-strategy-lab pytest labs/07-rag-retrieval-strategy-lab/tests
```

## Tradeoffs

- Small synthetic corpus (~20 documents) keeps the lab reproducible without a real dataset.
- Embeddings are generated with `sentence-transformers` locally, no API key needed.
- Reranking and query expansion are stubbed in the scaffold; implement with a cross-encoder or LLM call.
