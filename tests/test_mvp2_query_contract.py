"""tests/test_mvp2_query_contract.py
==================================
MVP 2 tests for the retrieval query validation boundary.
"""

from __future__ import annotations

import pytest
from src.engines.retrieval.query_contract import RetrievalQuery, validate_query


def test_query_is_normalized_at_the_boundary() -> None:
    request = validate_query(
        query="  revenue by quarter  ",
        tenant_id=" tenant-a ",
        top_k=5,
    )
    assert isinstance(request, RetrievalQuery)
    assert request.query == "revenue by quarter"
    assert request.tenant_id == "tenant-a"
    assert request.top_k == 5
    assert request.document_ids == ()


@pytest.mark.parametrize("query", ["", " ", "\n\t"])
def test_empty_queries_are_rejected(query: str) -> None:
    with pytest.raises(ValueError):
        validate_query(query=query, tenant_id="tenant-a")


@pytest.mark.parametrize("top_k", [0, -1, 101, True])
def test_invalid_top_k_is_rejected(top_k: int) -> None:
    with pytest.raises((ValueError, TypeError)):
        validate_query(
            query="test",
            tenant_id="tenant-a",
            top_k=top_k,
        )


def test_document_filter_duplicates_are_removed() -> None:
    request = validate_query(
        query="test query",
        tenant_id="tenant-a",
        document_ids=("doc-1", "doc-2", "doc-1", "  doc-3  "),
    )
    assert request.document_ids == ("doc-1", "doc-2", "doc-3")


def test_type_errors_on_invalid_argument_types() -> None:
    with pytest.raises(TypeError, match="query must be a string"):
        validate_query(query=123, tenant_id="tenant-a")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="tenant_id must be a string"):
        validate_query(query="valid", tenant_id=None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="tenant_id must not be empty"):
        validate_query(query="valid", tenant_id="   ")

    with pytest.raises(TypeError, match="document_ids must be a sequence"):
        validate_query(query="valid", tenant_id="tenant-a", document_ids="doc-1")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="document_ids must contain strings"):
        validate_query(query="valid", tenant_id="tenant-a", document_ids=[123])  # type: ignore[list-item]


def test_query_exceeding_max_chars_is_rejected() -> None:
    long_query = "a" * 4001
    with pytest.raises(ValueError, match="query exceeds the maximum length"):
        validate_query(query=long_query, tenant_id="tenant-a", max_query_chars=4000)
