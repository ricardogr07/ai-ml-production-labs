#!/usr/bin/env python3
"""
Smoke test for the CosmosDB LLM eval store.

Runs two paths:
  success path  -- full lifecycle write + read-back, verified with assertions
  error path    -- get_experiment for a missing id, verified to return None (not raise)

Usage:
  uv run python scripts/smoke_test.py --target local     # CosmosDB emulator
  uv run python scripts/smoke_test.py --target deployed  # Azure (reads COSMOS_URL / COSMOS_KEY)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
import warnings

import structlog
from azure.cosmos import CosmosClient, PartitionKey
from cosmosdb_llm_eval_store.cosmos_repository import CosmosDBEvalStoreRepository
from cosmosdb_llm_eval_store.schemas import EvaluationScore, Experiment, ModelResponse, PromptRun

from production_labs_shared.logging import configure_logging
from production_labs_shared.telemetry import timed_operation

logging.getLogger("azure").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

_EMULATOR_URL = "https://localhost:8081"
_EMULATOR_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
)


def _build_repo(target: str) -> CosmosDBEvalStoreRepository:
    if target == "local":
        url, key, verify = _EMULATOR_URL, _EMULATOR_KEY, False
    else:
        url = os.environ["COSMOS_URL"]
        key = os.environ["COSMOS_KEY"]
        verify = True

    database = os.environ.get("COSMOS_DATABASE", "llm-eval-store")
    container = os.environ.get("COSMOS_CONTAINER", "evaluations")

    client = CosmosClient(url=url, credential=key, connection_verify=verify)
    db = client.create_database_if_not_exists(database)
    db.create_container_if_not_exists(
        id=container,
        partition_key=PartitionKey(path="/experiment_id"),
    )
    return CosmosDBEvalStoreRepository(client, database, container)


def _success_path(repo: CosmosDBEvalStoreRepository, log: structlog.BoundLogger) -> None:  # type: ignore[type-arg]
    exp_id = f"smoke-{uuid.uuid4()}"
    log.info("smoke.success_path.start", experiment_id=exp_id)

    with timed_operation("save_experiment", experiment_id=exp_id):
        exp = Experiment(
            id=exp_id,
            experiment_id=exp_id,
            name="Smoke Test Experiment",
            description="Created by smoke_test.py",
        )
        repo.save_experiment(exp)
    log.info("smoke.experiment_saved", experiment_id=exp_id)

    run_id = str(uuid.uuid4())
    with timed_operation("save_prompt_run", experiment_id=exp_id):
        run = PromptRun(
            id=run_id,
            experiment_id=exp_id,
            prompt="What is the capital of France?",
            model_name="claude-sonnet-4-6",
            model_version="20250101",
        )
        repo.save_prompt_run(run)
    log.info("smoke.prompt_run_saved", experiment_id=exp_id, run_id=run_id)

    resp_id = str(uuid.uuid4())
    with timed_operation("save_response", experiment_id=exp_id):
        resp = ModelResponse(
            id=resp_id,
            experiment_id=exp_id,
            prompt_run_id=run_id,
            response_text="Paris",
            latency_ms=95.4,
            token_count=5,
        )
        repo.save_response(resp)
    log.info("smoke.response_saved", experiment_id=exp_id, resp_id=resp_id)

    with timed_operation("save_score", experiment_id=exp_id, metric="faithfulness"):
        repo.save_score(
            EvaluationScore(
                id=str(uuid.uuid4()),
                experiment_id=exp_id,
                response_id=resp_id,
                metric_name="faithfulness",
                score=1.0,
            )
        )
    log.info("smoke.score_saved", experiment_id=exp_id, metric="faithfulness", score=1.0)

    with timed_operation("get_experiment", experiment_id=exp_id):
        retrieved = repo.get_experiment(exp_id)

    assert retrieved is not None, "get_experiment returned None for a just-saved experiment"
    assert retrieved.name == "Smoke Test Experiment"
    log.info(
        "smoke.success_path.ok",
        experiment_id=exp_id,
        retrieved_name=retrieved.name,
    )


def _error_path(repo: CosmosDBEvalStoreRepository, log: structlog.BoundLogger) -> None:  # type: ignore[type-arg]
    missing_id = f"nonexistent-{uuid.uuid4()}"
    log.info("smoke.error_path.start", experiment_id=missing_id)

    with timed_operation("get_experiment_missing", experiment_id=missing_id):
        result = repo.get_experiment(missing_id)

    assert result is None, f"Expected None for missing experiment, got {result!r}"
    log.warning(
        "smoke.error_path.ok",
        experiment_id=missing_id,
        result=None,
        note="get_experiment returned None as expected for unknown id",
    )


def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    parser = argparse.ArgumentParser(description="Smoke test the CosmosDB eval store.")
    parser.add_argument(
        "--target",
        choices=["local", "deployed"],
        default="local",
        help="'local' uses the CosmosDB emulator; 'deployed' reads COSMOS_URL / COSMOS_KEY",
    )
    args = parser.parse_args()
    log.info("smoke.init", target=args.target)

    try:
        repo = _build_repo(args.target)
    except KeyError as exc:
        log.error("smoke.config_error", missing_env_var=str(exc))
        return 1

    try:
        _success_path(repo, log)
        _error_path(repo, log)
    except AssertionError as exc:
        log.error("smoke.assertion_failed", detail=str(exc))
        return 1

    log.info("smoke.all_paths_passed", target=args.target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
