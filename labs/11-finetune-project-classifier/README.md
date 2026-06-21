# Lab 11: Fine-tuned Project Classifier

## What this proves

Fine-tuning as a measurable adaptation strategy: take a small pretrained HuggingFace model, establish a baseline accuracy on a labeled dataset, fine-tune it, and show the before/after metric comparison. The domain is project type classification.

## Scope

- Capability: Fine-tune `distilbert-base-uncased` for 6-class project type classification
- Input: project description text
- Output: predicted label from `{cloud_api, ml_model, rag_system, agent_system, data_pipeline, observability}`
- Deployment target: local (GPU optional; runs on CPU with small dataset)
- Non-goals: production serving, model registry, real-world dataset

## Architecture

```text
labeled_dataset → baseline_eval (zero-shot) → baseline_accuracy
               → fine_tune (Trainer API) → fine_tuned_accuracy
               → before/after comparison table
```

## Run locally

```bash
uv sync
uv run --package finetune-project-classifier python labs/11-finetune-project-classifier/scripts/finetune.py
```

## Test

```bash
uv run --package finetune-project-classifier pytest labs/11-finetune-project-classifier/tests
```

## Tradeoffs

- Tiny synthetic dataset (18 samples): enough to show the fine-tuning pattern; real improvement requires hundreds of examples per class.
- CPU training is slow for transformers; use a GPU or Google Colab for real experiments.
- `distilbert-base-uncased` is the right size: small enough to train on CPU, large enough to demonstrate adaptation.
