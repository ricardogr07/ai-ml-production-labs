# Lab 06: Cosmos DB Vector Memory Lab

## What this proves

Embedding storage and vector similarity search backed by Azure Cosmos DB. The lab generates embeddings for a corpus of real Wikipedia articles on ML and vector-search topics using a local sentence-transformer model, stores documents with their embedding vectors, and runs similarity search, demonstrating the vector storage layer independently of any RAG framework or generation step.

## Scope

- Capability: store documents with embeddings and retrieve by similarity
- Input: text corpus and a query string
- Output: ranked list of similar documents with scores
- Deployment target: Azure Cosmos DB (DiskANN vector index)
- Non-goals: RAG pipeline, generation, HTTP API, UI

## Architecture

See [docs/architecture.md](docs/architecture.md) for component and sequence diagrams.

```
corpus -> SentenceTransformer -> CosmosDBVectorStoreRepository.add()
query  -> SentenceTransformer -> CosmosDBVectorStoreRepository.search() -> [SearchResult(doc, score)]
```

Two implementations share the `VectorStoreRepository` interface:

| Implementation | When to use |
|---|---|
| `InMemoryVectorStoreRepository` | Unit tests, quick local experiments |
| `CosmosDBVectorStoreRepository` | Integration tests (emulator) and Azure (DiskANN) |

## Tech stack

| Component | Library | Why |
|---|---|---|
| Vector store | `azure-cosmos >= 4.7` | DiskANN index, serverless billing, native float32 array storage |
| Embeddings | `sentence-transformers >= 3.0` | Local model, no API key, 384-dim all-MiniLM-L6-v2 |
| Schemas | `pydantic >= 2.7` | Validated document and result models |
| Config | `production-labs-shared` | Env-var binding via BaseLabSettings |

## Prerequisites

- Docker (for the CosmosDB emulator)
- Python 3.12 via `uv`

The `all-MiniLM-L6-v2` model (~90 MB) downloads automatically on first run of `seed_data.py`.

## Run locally

```bash
# Start the CosmosDB emulator (port 8082)
docker compose up -d

# Wait for the emulator to be healthy, then seed the corpus
uv run python labs/06-cosmosdb-vector-memory-lab/scripts/seed_data.py

# Run a smoke test against the emulator
uv run python labs/06-cosmosdb-vector-memory-lab/scripts/smoke_test.py
```

The seed corpus (`data/wikipedia_corpus.json`) is 12 real Wikipedia article
extracts on ML and vector-search topics (machine learning, embeddings, vector
databases, semantic search, RAG, cosine similarity, DiskANN, etc.), content
from Wikipedia, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
To refresh it, run `scripts/fetch_wikipedia_corpus.py` (one-off, stdlib only,
not part of any test or CI path).

## Test

```bash
# Unit tests (no emulator required)
uv run pytest labs/06-cosmosdb-vector-memory-lab/tests/unit -m unit

# Integration tests (requires: docker compose up -d)
uv run pytest labs/06-cosmosdb-vector-memory-lab/tests/integration -m integration

# All tests via tox
tox -e py312
```

## Environment variables

| Name | Default | Description |
|---|---|---|
| `COSMOS_URL` | `https://localhost:8082` | CosmosDB account endpoint |
| `COSMOS_KEY` | emulator key | CosmosDB primary key |
| `COSMOS_DATABASE` | `vector-memory` | Database name |
| `COSMOS_CONTAINER` | `documents` | Container name |

Copy `.env.example` to `.env` and fill in values for Azure deployment.

## Emulator limitation

The CosmosDB Linux emulator does not support `VectorEmbeddingPolicy` or the `VectorDistance()` SQL function. Integration tests and the local smoke test use a Python cosine similarity fallback (`use_vector_index=False`). The full DiskANN path requires a real Azure account and is covered by the E2E test (`tests/e2e/`) and CI smoke test (`--target deployed`).

## Production notes

- **Partition key**: `/id`. Documents are partitioned by their own id since there is no natural grouping key.
- **Serverless mode**: no throughput pre-provisioning; suits bursty workloads under ~1,000 RU/s average.
- **DiskANN dimension**: must be 384 (matching `all-MiniLM-L6-v2`). Changing the embedding model requires recreating the container with a new `VectorEmbeddingPolicy`.
- **Scale**: brute-force cosine is adequate under ~1,000 documents. DiskANN scales to tens of millions of vectors.

## Tradeoffs

- `InMemoryVectorStoreRepository` uses brute-force cosine similarity, fine for fewer than 1,000 documents.
- Cosmos DB DiskANN scales to millions of vectors but requires a real Azure account.
- `sentence-transformers` embeddings are generated locally with no OpenAI API key.
