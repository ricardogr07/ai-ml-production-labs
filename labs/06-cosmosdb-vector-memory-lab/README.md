# Lab 06: Cosmos DB Vector Memory Lab

## What this proves

Embedding storage and vector similarity search backed by Azure Cosmos DB. The lab generates embeddings for a small corpus, stores documents with their embedding vectors, and runs similarity search, demonstrating the vector storage layer independently of any RAG framework.

## Scope

- Capability: Store documents with embeddings and retrieve by similarity
- Input: text corpus + a query
- Output: ranked list of similar documents with scores
- Deployment target: Azure Cosmos DB (vector index)
- Non-goals: RAG pipeline, generation, UI

## Architecture

```text
corpus → EmbeddingService → InMemoryVectorStore / CosmosVectorStore
query → embed → similarity_search → [SearchResult(doc, score), ...]
```

## Run locally

```bash
uv sync
uv run --package cosmosdb-vector-memory-lab python labs/06-cosmosdb-vector-memory-lab/scripts/seed_data.py
```

## Test

```bash
uv run --package cosmosdb-vector-memory-lab pytest labs/06-cosmosdb-vector-memory-lab/tests
```

## Tradeoffs

- `InMemoryVectorStore` uses brute-force cosine similarity, fine for < 1,000 documents.
- Cosmos DB vector index (DiskANN) scales to millions of vectors but requires a real Azure account.
- `sentence-transformers` embeddings are generated locally, no OpenAI API key needed.
