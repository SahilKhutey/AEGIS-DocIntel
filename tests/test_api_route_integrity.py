"""
API route integrity — a *ratchet* on known duplicate routes.

Background (verified by walking the live app's route tree):
  Two parallel API trees are mounted — ``src/api/routers/`` (the /v1 REST API) and
  ``src/api/routes/query.py`` (the legacy AEL tree) — and they claim the SAME
  (method, path) pairs. Starlette dispatches to the first registered handler, so the
  second handler is dead code, and for ``POST /v1/query`` the *AEL* query endpoint is
  completely unreachable (its integration test sees the documents-query schema).

These tests do NOT claim that is fine. They freeze the current set so that:
  1. no NEW collision or duplicate operation id can be introduced, and
  2. when API consolidation (Phase 3) removes one, the test FAILS until the entry is
     deleted from the allowlist below — the list can only ever shrink.
"""
from __future__ import annotations

import re
import warnings
from collections import defaultdict

import pytest

from src.api.route_inspect import iter_operations
from src.main import app

# (method, path) -> handlers that claim it. Ordered as registered: the FIRST one wins.
KNOWN_COLLISIONS: dict[tuple[str, str], tuple[str, ...]] = {
    ("DELETE", "/v1/documents/{doc_id}"): ("routers.documents.delete_document", "routes.query.delete_document"),
    ("GET", "/v1/documents"): ("routers.documents.list_documents", "routes.query.list_documents"),
    ("GET", "/v1/documents/{doc_id}/elements"): ("routers.documents.get_elements", "routes.query.get_elements"),
    ("POST", "/v1/advanced/compliance/pii-scan"): (
        "routers.advanced_features.scan_and_redact_pii",
        "routers.advanced_features.scan_pii_entities",
    ),
    ("POST", "/v1/query"): ("routers.queries.query_documents", "routes.query.query"),
}

KNOWN_DUPLICATE_OPERATION_IDS = {
    "delete_document_v1_documents__doc_id__delete",
    "get_elements_v1_documents__doc_id__elements_get",
    "list_documents_v1_documents_get",
}


@pytest.fixture(scope="module")
def operations():
    ops = list(iter_operations(app.routes))
    assert len(ops) > 30, f"route walker found only {len(ops)} operations — walker is broken, not the API"
    return ops


def _collisions(ops):
    seen: dict[tuple[str, str], list[str]] = defaultdict(list)
    for method, path, handler in ops:
        seen[(method, path)].append(handler)
    return {k: tuple(v) for k, v in seen.items() if len(v) > 1}


def test_no_new_route_collisions(operations):
    current = _collisions(operations)
    new = {k: v for k, v in current.items() if k not in KNOWN_COLLISIONS}
    assert not new, (
        "NEW duplicate (method, path) registrations — the second handler can never run:\n"
        + "\n".join(f"  {m} {p} -> {h}" for (m, p), h in sorted(new.items()))
    )


def test_resolved_collisions_are_removed_from_the_allowlist(operations):
    """The ratchet: fixing a collision must be accompanied by shrinking KNOWN_COLLISIONS."""
    current = _collisions(operations)
    resolved = sorted(k for k in KNOWN_COLLISIONS if k not in current)
    assert not resolved, (
        f"These collisions are fixed — delete them from KNOWN_COLLISIONS in this file: {resolved}"
    )


def test_known_collision_handlers_unchanged(operations):
    current = _collisions(operations)
    for key, handlers in KNOWN_COLLISIONS.items():
        assert current.get(key) == handlers, f"{key}: handlers changed to {current.get(key)}; update the allowlist"


def test_ael_query_is_shadowed_documented():
    """Pins the *consequence* of the POST /v1/query collision so nobody 'discovers' it again:
    the first-registered (documents) handler wins, so the AEL handler is unreachable."""
    handlers = KNOWN_COLLISIONS[("POST", "/v1/query")]
    assert handlers[0] == "routers.queries.query_documents"
    assert handlers[1] == "routes.query.query"


def test_duplicate_operation_ids_ratchet():
    app.openapi_schema = None  # openapi() caches; force regeneration so warnings fire
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        app.openapi()
    found = {
        m.group(1)
        for w in caught
        if (m := re.search(r"Duplicate Operation ID (\S+)", str(w.message)))
    }
    new = found - KNOWN_DUPLICATE_OPERATION_IDS
    fixed = KNOWN_DUPLICATE_OPERATION_IDS - found
    assert not new, f"NEW duplicate OpenAPI operation ids (breaks client generators): {sorted(new)}"
    assert not fixed, f"Fixed — remove from KNOWN_DUPLICATE_OPERATION_IDS: {sorted(fixed)}"
