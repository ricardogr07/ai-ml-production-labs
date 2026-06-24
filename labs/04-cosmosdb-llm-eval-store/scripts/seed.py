#!/usr/bin/env python3
"""Seed the CosmosDB eval store with sample experiments and evaluation data."""

from __future__ import annotations

import logging
import os
import sys
import uuid
import warnings

from azure.cosmos import CosmosClient, PartitionKey
from cosmosdb_llm_eval_store.cosmos_repository import CosmosDBEvalStoreRepository
from cosmosdb_llm_eval_store.schemas import (
    EvaluationScore,
    Experiment,
    ModelResponse,
    PromptRun,
)

from production_labs_shared.logging import configure_logging
from production_labs_shared.telemetry import timed_operation

logging.getLogger("azure").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_EMULATOR_URL = "https://localhost:8081"
_EMULATOR_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)

_PROMPTS = [
    "Summarize the quarterly earnings report.",
    "What are the key risks mentioned in the filing?",
]
_METRICS = ["faithfulness", "relevance"]
_SCORES = [0.92, 0.85, 0.78, 0.95]


def _build_client() -> tuple[CosmosClient, bool]:
    url = os.environ.get("COSMOS_URL", _EMULATOR_URL)
    key = os.environ.get("COSMOS_KEY", _EMULATOR_KEY)
    is_emulator = url == _EMULATOR_URL
    client = CosmosClient(url=url, credential=key, connection_verify=not is_emulator)
    return client, is_emulator


def seed() -> None:
    import structlog

    log = structlog.get_logger()
    configure_logging()

    client, is_emulator = _build_client()
    database = os.environ.get("COSMOS_DATABASE", "llm-eval-store")
    container = os.environ.get("COSMOS_CONTAINER", "evaluations")

    db = client.create_database_if_not_exists(database)
    db.create_container_if_not_exists(
        id=container,
        partition_key=PartitionKey(path="/experiment_id"),
    )

    repo = CosmosDBEvalStoreRepository(client, database, container)
    log.info("seed.start", target="emulator" if is_emulator else "azure", database=database)

    score_idx = 0
    for exp_num in range(1, 3):
        exp_id = f"exp-{exp_num:03d}"

        with timed_operation("save_experiment", experiment_id=exp_id):
            repo.save_experiment(
                Experiment(
                    id=exp_id,
                    experiment_id=exp_id,
                    name=f"Experiment {exp_num}",
                    description=f"Sample evaluation run {exp_num}.",
                )
            )
        log.info("seed.experiment_saved", experiment_id=exp_id)

        for prompt in _PROMPTS:
            run_id = str(uuid.uuid4())
            with timed_operation("save_prompt_run", experiment_id=exp_id):
                run = PromptRun(
                    id=run_id,
                    experiment_id=exp_id,
                    prompt=prompt,
                    model_name="claude-sonnet-4-6",
                    model_version="20250101",
                )
                repo.save_prompt_run(run)
            log.info("seed.prompt_run_saved", experiment_id=exp_id, run_id=run_id)

            resp_id = str(uuid.uuid4())
            with timed_operation("save_response", experiment_id=exp_id):
                resp = ModelResponse(
                    id=resp_id,
                    experiment_id=exp_id,
                    prompt_run_id=run_id,
                    response_text="This is a generated model response.",
                    latency_ms=round(200 + exp_num * 50.0, 1),
                    token_count=35 + exp_num * 5,
                )
                repo.save_response(resp)
            log.info("seed.response_saved", experiment_id=exp_id, resp_id=resp_id)

            for metric in _METRICS:
                score_val = _SCORES[score_idx % len(_SCORES)]
                score_idx += 1
                with timed_operation("save_score", experiment_id=exp_id, metric=metric):
                    repo.save_score(
                        EvaluationScore(
                            id=str(uuid.uuid4()),
                            experiment_id=exp_id,
                            response_id=resp_id,
                            metric_name=metric,
                            score=score_val,
                        )
                    )
                log.info(
                    "seed.score_saved",
                    experiment_id=exp_id,
                    metric=metric,
                    score=score_val,
                )

    log.info("seed.complete")


if __name__ == "__main__":
    sys.exit(seed() or 0)
