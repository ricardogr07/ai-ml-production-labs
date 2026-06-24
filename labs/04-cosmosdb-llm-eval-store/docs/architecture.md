# Architecture: CosmosDB LLM Eval Store

## Component Overview

```mermaid
graph TD
    subgraph Library
        S[Settings<br/>config.py]
        R[EvalStoreRepository<br/>ABC]
        IM[InMemoryEvalStoreRepository<br/>for tests]
        CR[CosmosDBEvalStoreRepository<br/>for production]
    end

    subgraph Schemas
        E[Experiment]
        PR[PromptRun]
        MR[ModelResponse]
        ES[EvaluationScore]
    end

    subgraph Infrastructure
        EMU[CosmosDB Linux Emulator<br/>docker-compose.yml]
        AZ[Azure CosmosDB<br/>Serverless / Session]
    end

    S --> CR
    R --> IM
    R --> CR
    CR -->|upsert / read / query| EMU
    CR -->|upsert / read / query| AZ
    E & PR & MR & ES -->|model_dump| CR
```

## Data Flow: Evaluation Lifecycle

```mermaid
sequenceDiagram
    participant Client
    participant Repo as CosmosDBEvalStoreRepository
    participant Cosmos as Azure CosmosDB

    Client->>Repo: save_experiment(Experiment)
    Repo->>Cosmos: upsert_item {document_type: "experiment"}

    Client->>Repo: save_prompt_run(PromptRun)
    Repo->>Cosmos: upsert_item {document_type: "prompt_run"}

    Client->>Repo: save_response(ModelResponse)
    Repo->>Cosmos: upsert_item {document_type: "model_response"}

    Client->>Repo: save_score(EvaluationScore)
    Repo->>Cosmos: upsert_item {document_type: "evaluation_score"}

    Client->>Repo: list_scores(experiment_id)
    Repo->>Cosmos: SQL WHERE experiment_id=? AND document_type="evaluation_score"
    Cosmos-->>Repo: [EvaluationScore, ...]
    Repo-->>Client: list[EvaluationScore]
```

## Document Hierarchy

```mermaid
erDiagram
    Experiment {
        string id PK
        string experiment_id
        string name
        string description
        string status
        string document_type
    }
    PromptRun {
        string id PK
        string experiment_id FK
        string prompt
        string model_name
        string model_version
        string document_type
    }
    ModelResponse {
        string id PK
        string experiment_id FK
        string prompt_run_id FK
        string response_text
        float latency_ms
        int token_count
        string document_type
    }
    EvaluationScore {
        string id PK
        string experiment_id FK
        string response_id FK
        string metric_name
        float score
        string evaluator
        string document_type
    }

    Experiment ||--o{ PromptRun : "experiment_id"
    PromptRun ||--o{ ModelResponse : "prompt_run_id"
    ModelResponse ||--o{ EvaluationScore : "response_id"
```

## Technology Decisions

### Single-container, multi-type pattern

All four document types (`experiment`, `prompt_run`, `model_response`, `evaluation_score`) live in
one Cosmos DB container partitioned by `/experiment_id`. This means every document belonging to
one experiment is co-located on the same physical partition, which makes queries like
"all scores for experiment X" zero-cost fan-outs.

The `document_type` field on every schema is required because Cosmos DB SQL does not have a native
type system. Without it, a query for scores would return all documents in the partition.

Trade-off: cross-experiment aggregations (e.g., average score across all experiments) require
`enable_cross_partition_query=True` and are more expensive. For this workload, per-experiment
queries dominate, so this trade-off is acceptable.

### Serverless capacity mode

The infrastructure is provisioned in Serverless mode so there is no minimum cost when the store
is idle. For high-throughput production workloads with sustained RU/s, switching to provisioned
throughput would reduce per-operation cost.

### Repository pattern

`EvalStoreRepository` is an ABC so the library can be tested without a running Cosmos DB instance.
`InMemoryEvalStoreRepository` is used in unit tests; `CosmosDBEvalStoreRepository` is used in
integration tests (via the Docker emulator) and in production. The scripts and smoke test both
use the Cosmos implementation, so any divergence between the two would surface immediately.

### Emulator portability

The CosmosDB Linux Emulator (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`) exposes
the identical SQL API as the Azure service. Scripts and integration tests written against the
emulator require no code changes when pointed at Azure; only connection settings change.
