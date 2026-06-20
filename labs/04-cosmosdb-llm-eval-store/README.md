# Lab 04: Cosmos DB LLM Evaluation Store

## What this proves

A real persistence model for AI evaluation workflows using Azure Cosmos DB (NoSQL API). The document schema captures the full evaluation lifecycle: experiments, prompt runs, model responses, evaluation scores, and human reviews, all partitioned by `experiment_id` for efficient querying.

## Scope

- Capability: NoSQL document model for LLM evaluation
- Input: experiment runs, model responses, evaluation scores
- Output: queryable evaluation records in Cosmos DB
- Deployment target: Azure Cosmos DB (serverless tier)
- Non-goals: UI, real LLM calls, automated evaluation metrics

## Architecture

```text
seed_data.py → InMemoryRepository / CosmosRepository → Cosmos DB (/experiment_id partition)

Experiment
  └─ PromptRun
       └─ ModelResponse
            └─ EvaluationScore
```

## Documents

| Document | Partition key | Purpose |
|---|---|---|
| Experiment | /experiment_id | Evaluation experiment metadata |
| PromptRun | /experiment_id | Individual prompt sent to a model |
| ModelResponse | /experiment_id | Model response with latency and tokens |
| EvaluationScore | /experiment_id | Metric score (auto or human) |

## Run locally

```bash
uv sync
uv run --package cosmosdb-llm-eval-store python labs/04-cosmosdb-llm-eval-store/scripts/seed_data.py
```

## Test

```bash
uv run --package cosmosdb-llm-eval-store pytest labs/04-cosmosdb-llm-eval-store/tests
```

## Tradeoffs

- `InMemoryEvalStoreRepository` enables tests without Cosmos DB.
- Partition key `/experiment_id` optimizes for "all documents in an experiment" queries; cross-experiment aggregation is expensive.
- Cosmos DB serverless tier has lower throughput limits, fine for lab-scale data.
