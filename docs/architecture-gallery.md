# Architecture Gallery

Each lab's canonical data flow.

---

## Lab 01: FastAPI Azure ML Service

```text
client -> FastAPI (/predict) -> PredictionService -> rule-based scorer -> PredictResponse
               |
           /health -> HealthResponse
```

Deploy target: Azure Container Apps

---

## Lab 02: Azure Functions Text Classifier

```text
HTTP trigger -> classify() -> sklearn model -> ClassificationResponse
```

Deploy target: Azure Functions (Consumption plan)

---

## Lab 03: FastMCP Portfolio Tools

```text
MCP client -> FastMCP server -> tool dispatcher
               |- score_project()
               |- suggest_readme_sections()
               +- generate_portfolio_summary()
```

---

## Lab 04: Cosmos DB LLM Eval Store

```text
seed_data.py -> CosmosRepository -> Cosmos DB (partition: /experiment_id)
                    ^
              Experiment -> PromptRun -> ModelResponse -> EvaluationScore
```

---

## Lab 05: Ollama Local LLM API

```text
client -> FastAPI (/summarize) -> OllamaClient -> local Ollama -> structured response
```

---

## Lab 06: Cosmos DB Vector Memory Lab

```text
corpus -> EmbeddingService -> CosmosVectorRepository -> vector index
                                                            |
query -> embed() -> similarity_search() -> ranked results
```

---

## Lab 07: RAG Retrieval Strategy Lab

```text
corpus -> chunker -> vector store
golden queries -> [naive | filtered | reranked | query-expanded] retrieval
                                                   |
                                       Recall@3 / MRR / latency table
```

---

## Lab 08: LangGraph Project Agent

```text
project_idea
  -> classify_project_type
  -> score_against_portfolio_thesis
  -> identify_missing_artifacts
  -> generate_implementation_plan
  -> return_scorecard
```

---

## Lab 09: LlamaIndex Doc Q&A

```text
markdown docs -> LlamaIndex ingestion -> vector index
user question -> query engine -> answer + source chunks
```

---

## Lab 10: MLflow Classifier API

```text
synthetic dataset -> train.py -> MLflow experiment -> model artifact
                                                          |
                                   FastAPI (/predict) -> model.predict()
```

---

## Lab 11: Fine-tuned Project Classifier

```text
labeled dataset -> baseline HF model -> evaluate -> baseline metrics
                -> fine-tune -> evaluate -> fine-tuned metrics -> comparison table
```

---

## Lab 12: ML Drift Monitoring Lab

```text
reference dataset -> drift_monitor.py -> current dataset (shifted)
                                               |
                                      drift report + feature alerts
```

---

## Lab 13: FastAPI OpenTelemetry Lab

```text
client -> FastAPI -> OTel SDK -> console exporter (local) / Azure Monitor (prod)
                       |
               traces + metrics + structured logs
```

---

## Lab 14: Portfolio AI Production Capstone

```text
client -> FastAPI (OTel instrumented)
             |
        LangGraph agent
             |- Cosmos DB (RAG memory)
             |- Ollama / HF model
             +- MLflow model artifact
             |
        structured response + evaluation score
             |
        Azure Container Apps + Application Insights
```
