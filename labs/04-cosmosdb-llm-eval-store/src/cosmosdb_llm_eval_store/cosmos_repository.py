"""Azure Cosmos DB implementation of the eval store repository."""

from __future__ import annotations

from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from cosmosdb_llm_eval_store.repository import EvalStoreRepository
from cosmosdb_llm_eval_store.schemas import EvaluationScore, Experiment, ModelResponse, PromptRun


class CosmosDBEvalStoreRepository(EvalStoreRepository):
    def __init__(self, client: CosmosClient, database: str, container: str) -> None:
        self._container = client.get_database_client(database).get_container_client(container)

    def save_experiment(self, experiment: Experiment) -> None:
        self._container.upsert_item(experiment.model_dump(mode="json"))

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        try:
            item = self._container.read_item(item=experiment_id, partition_key=experiment_id)
            return Experiment(**item)
        except CosmosResourceNotFoundError:
            return None

    def save_prompt_run(self, run: PromptRun) -> None:
        self._container.upsert_item(run.model_dump(mode="json"))

    def save_response(self, response: ModelResponse) -> None:
        self._container.upsert_item(response.model_dump(mode="json"))

    def save_score(self, score: EvaluationScore) -> None:
        self._container.upsert_item(score.model_dump(mode="json"))

    def list_scores(self, experiment_id: str) -> list[EvaluationScore]:
        return [
            EvaluationScore(**item)
            for item in self._container.query_items(
                query=(
                    "SELECT * FROM c "
                    "WHERE c.experiment_id = @experiment_id "
                    "AND c.document_type = @doc_type"
                ),
                parameters=[
                    {"name": "@experiment_id", "value": experiment_id},
                    {"name": "@doc_type", "value": "evaluation_score"},
                ],
                enable_cross_partition_query=False,
            )
        ]

    def list_prompt_runs(self, experiment_id: str) -> list[PromptRun]:
        return [
            PromptRun(**item)
            for item in self._container.query_items(
                query=(
                    "SELECT * FROM c "
                    "WHERE c.experiment_id = @experiment_id "
                    "AND c.document_type = @doc_type"
                ),
                parameters=[
                    {"name": "@experiment_id", "value": experiment_id},
                    {"name": "@doc_type", "value": "prompt_run"},
                ],
                enable_cross_partition_query=False,
            )
        ]

    def list_responses(self, experiment_id: str) -> list[ModelResponse]:
        return [
            ModelResponse(**item)
            for item in self._container.query_items(
                query=(
                    "SELECT * FROM c "
                    "WHERE c.experiment_id = @experiment_id "
                    "AND c.document_type = @doc_type"
                ),
                parameters=[
                    {"name": "@experiment_id", "value": experiment_id},
                    {"name": "@doc_type", "value": "model_response"},
                ],
                enable_cross_partition_query=False,
            )
        ]
