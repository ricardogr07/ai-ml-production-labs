# Lab 06: Architecture

## Component diagram

```mermaid
graph TD
    Settings["Settings\n(BaseLabSettings)"]
    ABC["VectorStoreRepository\n(ABC)"]
    InMem["InMemoryVectorStoreRepository"]
    Cosmos["CosmosDBVectorStoreRepository"]
    Emulator["CosmosDB Emulator\n(CRUD only, port 8082)"]
    Azure["Azure CosmosDB\n(DiskANN vector index)"]

    Settings --> Cosmos
    ABC --> InMem
    ABC --> Cosmos
    Cosmos -->|use_vector_index=False| Emulator
    Cosmos -->|use_vector_index=True| Azure
```

## Seed and query flow

```mermaid
sequenceDiagram
    participant S as seed_data.py
    participant M as SentenceTransformer
    participant R as CosmosDBVectorStoreRepository
    participant DB as CosmosDB

    S->>M: encode(corpus texts)
    M-->>S: embeddings (384-dim float32)
    S->>R: add(Document(id, content, embedding))
    R->>DB: upsert_item(document)

    S->>M: encode(query)
    M-->>S: query_embedding
    S->>R: search(query_embedding, top_k=3)
    R->>DB: VectorDistance() ORDER BY (Azure) or SELECT * + cosine (emulator)
    DB-->>R: ranked items
    R-->>S: list[SearchResult]
```

## Design notes

**DiskANN vs brute-force cosine**

`InMemoryVectorStoreRepository` and the `use_vector_index=False` fallback in `CosmosDBVectorStoreRepository` both compute cosine similarity in Python across all documents. This is fine for corpora under ~1,000 documents. `CosmosDBVectorStoreRepository` with `use_vector_index=True` delegates to Azure Cosmos DB's DiskANN index, which scales to tens of millions of vectors with sub-millisecond latency.

**Emulator limitation**

The CosmosDB Linux emulator does not support `VectorEmbeddingPolicy` or the `VectorDistance()` SQL function. Integration tests always run with `use_vector_index=False`. Only the E2E test (`tests/e2e/`) and deployed smoke test use the DiskANN path.

**Partition key**

The container uses `/id` as the partition key. Each document is its own logical partition since documents do not share a natural grouping key. This matches the serverless capacity mode, which has no cross-partition throughput limit at small scale.

**Embedding model and dimension**

The lab uses `all-MiniLM-L6-v2` from `sentence-transformers` (384-dim, cosine distance). This model runs locally with no API key. The Terraform `dimensions = 384` must stay in sync with this model; using a different model would cause Azure to reject upserts with a dimension mismatch error.
