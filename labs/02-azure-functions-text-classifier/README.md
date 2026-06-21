# Lab 02: Azure Functions Text Classifier

## What this proves

Serverless Python inference endpoint using Azure Functions HTTP trigger. The classifier runs on demand with zero idle cost, demonstrating when serverless is the right deployment shape for small inference workloads.

## Scope

- Capability: Text classification via Azure Functions HTTP trigger
- Input: `{ "text": "..." }`
- Output: `{ "label": "...", "confidence": ..., "model_version": "..." }`
- Deployment target: Azure Functions (Consumption plan)
- Non-goals: model training, persistence, streaming

## Architecture

```text
client → HTTP POST /api/classify → Azure Function → classifier → JSON response
```

## Run locally

```bash
uv sync
func start  # requires Azure Functions Core Tools
```

## Test

```bash
uv run --package azure-functions-text-classifier pytest labs/02-azure-functions-text-classifier/tests
```

## Tradeoffs

- Serverless cold starts add ~500ms on first request, acceptable for low-traffic inference.
- No model artifact: uses deterministic rules to keep scope on the Functions deployment pattern.
- Container Apps (Lab 01) is better when warm latency matters; Functions is better when near-zero idle cost matters.
