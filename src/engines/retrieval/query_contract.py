"""Validation for retrieval requests.

This module is deliberately independent of FastAPI and storage.
Authorization must still be enforced by the calling service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    query: str
    tenant_id: str
    top_k: int = 5
    document_ids: Tuple[str, ...] = ()


def validate_query(
    *,
    query: str,
    tenant_id: str,
    top_k: int = 5,
    document_ids: Sequence[str] = (),
    max_query_chars: int = 4000,
    max_top_k: int = 100,
) -> RetrievalQuery:
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")
    if len(normalized_query) > max_query_chars:
        raise ValueError(f"query exceeds the maximum length of {max_query_chars} characters")

    if not isinstance(tenant_id, str):
        raise TypeError("tenant_id must be a string")
    normalized_tenant = tenant_id.strip()
    if not normalized_tenant:
        raise ValueError("tenant_id must not be empty")

    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise TypeError("top_k must be an integer")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    if top_k > max_top_k:
        raise ValueError(f"top_k must not exceed {max_top_k}")

    if not isinstance(document_ids, (tuple, list, set)):
        raise TypeError("document_ids must be a sequence of strings")

    deduped_docs: list[str] = []
    for d in document_ids:
        if not isinstance(d, str):
            raise TypeError("document_ids must contain strings")
        clean_d = d.strip()
        if clean_d and clean_d not in deduped_docs:
            deduped_docs.append(clean_d)

    return RetrievalQuery(
        query=normalized_query,
        tenant_id=normalized_tenant,
        top_k=top_k,
        document_ids=tuple(deduped_docs),
    )
