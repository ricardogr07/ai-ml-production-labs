from __future__ import annotations

import pytest
from rag_retrieval_strategy_lab.query_expansion import expand_query


@pytest.mark.unit
def test_expand_query_adds_synonyms_for_known_term() -> None:
    result = expand_query("How is AI trained?")

    assert "artificial intelligence" in result
    assert "machine learning" in result
    assert result.startswith("How is AI trained?")


@pytest.mark.unit
def test_expand_query_returns_unchanged_when_no_match() -> None:
    result = expand_query("completely unrelated query text")

    assert result == "completely unrelated query text"


@pytest.mark.unit
def test_expand_query_deduplicates_overlapping_synonyms() -> None:
    result = expand_query("What happens when a star explodes in space?")

    # both "star" and "space" trigger overlapping synonym sets
    assert result.count("supernova") == 1
    assert result.count("neutron star") == 1
