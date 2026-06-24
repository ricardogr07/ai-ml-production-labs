"""Abstract repository interface for the LLM evaluation store."""

from __future__ import annotations

from abc import ABC, abstractmethod

from cosmosdb_llm_eval_store.schemas import EvaluationScore, Experiment, ModelResponse, PromptRun


class EvalStoreRepository(ABC):
    @abstractmethod
    def save_experiment(self, experiment: Experiment) -> None: ...

    @abstractmethod
    def get_experiment(self, experiment_id: str) -> Experiment | None: ...

    @abstractmethod
    def save_prompt_run(self, run: PromptRun) -> None: ...

    @abstractmethod
    def save_response(self, response: ModelResponse) -> None: ...

    @abstractmethod
    def save_score(self, score: EvaluationScore) -> None: ...

    @abstractmethod
    def list_scores(self, experiment_id: str) -> list[EvaluationScore]: ...

    @abstractmethod
    def list_prompt_runs(self, experiment_id: str) -> list[PromptRun]: ...

    @abstractmethod
    def list_responses(self, experiment_id: str) -> list[ModelResponse]: ...


class InMemoryEvalStoreRepository(EvalStoreRepository):
    """Local in-memory implementation for tests and local development."""

    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._runs: list[PromptRun] = []
        self._responses: list[ModelResponse] = []
        self._scores: list[EvaluationScore] = []

    def save_experiment(self, experiment: Experiment) -> None:
        self._experiments[experiment.experiment_id] = experiment

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def save_prompt_run(self, run: PromptRun) -> None:
        self._runs.append(run)

    def save_response(self, response: ModelResponse) -> None:
        self._responses.append(response)

    def save_score(self, score: EvaluationScore) -> None:
        self._scores.append(score)

    def list_scores(self, experiment_id: str) -> list[EvaluationScore]:
        return [s for s in self._scores if s.experiment_id == experiment_id]

    def list_prompt_runs(self, experiment_id: str) -> list[PromptRun]:
        return [r for r in self._runs if r.experiment_id == experiment_id]

    def list_responses(self, experiment_id: str) -> list[ModelResponse]:
        return [r for r in self._responses if r.experiment_id == experiment_id]
