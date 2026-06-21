# Lab 09: LlamaIndex Document Q&A

## What this proves

Document Q&A over local markdown files (project READMEs) with cited source chunks using LlamaIndex. The lab demonstrates focused document ingestion, chunking, indexing, and traceable retrieval, making hallucination easier to detect by always showing source chunks alongside answers.

## Scope

- Capability: Answer questions about project READMEs with source attribution
- Input: local markdown files + a natural language question
- Output: answer text + list of source chunks with file and similarity score
- Deployment target: local (CLI)
- Non-goals: web UI, real-time ingestion, multi-hop reasoning

## Architecture

```text
docs/*.md → LlamaIndex ingestion (chunked) → VectorStoreIndex
question → query engine → answer + source nodes
```

## Run locally

```bash
uv sync
uv run --package llamaindex-doc-qa-lab python labs/09-llamaindex-doc-qa-lab/scripts/query.py "What does lab 07 prove?"
```

## Test

```bash
uv run --package llamaindex-doc-qa-lab pytest labs/09-llamaindex-doc-qa-lab/tests
```

## Tradeoffs

- In-memory index: fast to build, lost on restart. For persistence, add a Cosmos DB or Qdrant vector store.
- Chunking strategy affects answer quality significantly; chunk size and overlap are tunable parameters.
- Requires an Anthropic API key (`ANTHROPIC_API_KEY`) for the LLM generation step.
