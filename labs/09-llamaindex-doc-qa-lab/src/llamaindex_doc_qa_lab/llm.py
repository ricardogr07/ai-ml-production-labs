"""LLM factory: dispatches on settings.llm_provider (ollama or anthropic)."""

from __future__ import annotations

from functools import lru_cache

from llama_index.core.llms.llm import LLM

from llamaindex_doc_qa_lab.config import settings


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    if settings.llm_provider == "ollama":
        from llama_index.llms.ollama import Ollama

        # default request_timeout (30s) is too short for CPU inference plus
        # multi-chunk refine synthesis over more than one retrieved source.
        return Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            request_timeout=180.0,
        )
    if settings.llm_provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic

        if settings.anthropic_api_key and settings.anthropic_api_key.get_secret_value():
            return Anthropic(
                model=settings.anthropic_model,
                api_key=settings.anthropic_api_key.get_secret_value(),
            )
        # falls back to ANTHROPIC_API_KEY from the process environment
        return Anthropic(model=settings.anthropic_model)
    raise ValueError(f"no LLM for provider {settings.llm_provider!r}")
