# Lab 04: CosmosDB LLM Eval Store

## What this proves

A production-grade persistence library for LLM evaluation workflows using Azure Cosmos DB (NoSQL
API). The document schema captures the full evaluation lifecycle: experiments, prompt runs, model
responses, and evaluation scores, all partitioned by `experiment_id` for efficient querying. The
repository pattern lets you test locally with an in-memory store and graduate to the real Cosmos
DB API via the official Docker emulator before deploying to Azure.

## Scope

- Type: Library (no HTTP endpoint, no server process)
- Input: experiment runs, model responses, evaluation scores
- Output: queryable evaluation records in Cosmos DB
- Deployment: Azure Cosmos DB (serverless tier) via Terraform
- Non-goals: UI, real LLM calls, automated evaluation metrics

## Tech stack

| Component | Choice | Reason |
|---|---|---|
| Document store | Azure Cosmos DB (NoSQL API) | Per-partition queries, serverless billing, JSON-native |
| Python SDK | azure-cosmos >= 4.7 | Official async-capable client |
| Schema validation | Pydantic v2 | Type-safe models, clean `model_dump` serialization |
| Local emulator | CosmosDB Linux Docker image | Identical SQL API, no Azure account needed for dev |
| Infrastructure | Terraform (azurerm ~> 3.110) | Reproducible serverless account + container provisioning |

## Document model

All four types share one container partitioned by `/experiment_id`. A `document_type` field on
every model enables SQL filtering within a partition.

```
Experiment  (document_type: "experiment")
  experiment_id, name, description, status, created_at

  PromptRun  (document_type: "prompt_run")
    experiment_id, prompt, model_name, model_version, created_at

    ModelResponse  (document_type: "model_response")
      experiment_id, prompt_run_id, response_text, latency_ms, token_count, created_at

      EvaluationScore  (document_type: "evaluation_score")
        experiment_id, response_id, metric_name, score, evaluator, created_at
```

## Local workflow (emulator)

**Step 1: start the emulator**

```bash
docker compose up -d
# wait ~60 s for the health check to pass
docker compose ps
```

**Step 2: seed sample data**

```bash
uv run python labs/04-cosmosdb-llm-eval-store/scripts/seed.py
```

**Step 3: run example SQL queries**

```bash
uv run python labs/04-cosmosdb-llm-eval-store/scripts/query_examples.py
```

**Step 4: run the smoke test (success + error path)**

```bash
uv run python labs/04-cosmosdb-llm-eval-store/scripts/smoke_test.py --target local
```

## Cloud workflow (Azure)

**Step 1: provision infrastructure**

```bash
terraform -chdir=labs/04-cosmosdb-llm-eval-store/infra init
terraform -chdir=labs/04-cosmosdb-llm-eval-store/infra apply
```

**Step 2: copy outputs to .env**

```bash
terraform -chdir=labs/04-cosmosdb-llm-eval-store/infra output endpoint
terraform -chdir=labs/04-cosmosdb-llm-eval-store/infra output -raw primary_key
```

Set `COSMOS_URL` and `COSMOS_KEY` in your `.env` (see `.env.example`).

**Step 3: run the smoke test against Azure**

```bash
uv run python labs/04-cosmosdb-llm-eval-store/scripts/smoke_test.py --target deployed
```

## Usage example

```python
from azure.cosmos import CosmosClient
from cosmosdb_llm_eval_store import CosmosDBEvalStoreRepository, Experiment, PromptRun

client = CosmosClient(url=COSMOS_URL, credential=COSMOS_KEY)
repo = CosmosDBEvalStoreRepository(client, database="llm-eval-store", container="evaluations")

exp = Experiment(id="exp-001", experiment_id="exp-001", name="My Eval", description="...")
repo.save_experiment(exp)

run = PromptRun(
    id="run-001",
    experiment_id="exp-001",
    prompt="Summarize this document.",
    model_name="claude-sonnet-4-6",
    model_version="20250101",
)
repo.save_prompt_run(run)

# Retrieve
retrieved = repo.get_experiment("exp-001")
runs = repo.list_prompt_runs("exp-001")
```

## Test

```bash
# Unit tests only (no Docker required)
pytest labs/04-cosmosdb-llm-eval-store -v -m unit

# Integration tests (emulator must be running)
pytest labs/04-cosmosdb-llm-eval-store -v -m integration

# Full tox gate
tox -e lint,type,py312,security,audit
```

## Production notes

- **Partition strategy**: `/experiment_id` co-locates all documents for an experiment on one
  physical partition. Per-experiment queries are cheap; cross-experiment aggregations require
  `enable_cross_partition_query=True` and fan out across all partitions.
- **Serverless vs. provisioned**: Serverless is cost-optimal for low or bursty workloads. Switch
  to provisioned throughput if you need consistent sub-10 ms latency at high RU/s.
- **Idempotency**: All writes use `upsert_item`, so re-running the seed or smoke test against
  an existing container is safe.
- **TLS**: `connection_verify=False` is set only for the local emulator (self-signed cert). Never
  use it against Azure.
