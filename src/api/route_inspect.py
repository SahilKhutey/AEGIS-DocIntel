"""
Route introspection helpers.

FastAPI >= 0.13x stores included routers lazily as ``_IncludedRouter`` objects, so
``app.routes`` no longer lists every operation — a naive loop over it sees only ~8 of ~60.
This walker descends through nested/included routers (applying their prefixes) and also
handles classic flattened route lists, so it works across FastAPI versions.

Used by the API-integrity and auth-coverage tests, and by scripts/list_routes.py.
"""
from __future__ import annotations

from typing import Iterator


def iter_operations(routes, prefix: str = "") -> Iterator[tuple[str, str, str]]:
    """Yield ``(METHOD, full_path, 'module.func')`` for every HTTP operation under *routes*."""
    for r in routes:
        if hasattr(r, "original_router"):  # _IncludedRouter (newer FastAPI)
            ctx = getattr(r, "include_context", None)
            yield from iter_operations(r.original_router.routes, prefix + (getattr(ctx, "prefix", "") or ""))
        elif getattr(r, "endpoint", None) is not None and getattr(r, "methods", None):
            ep = r.endpoint
            name = f"{ep.__module__.replace('src.api.', '')}.{ep.__name__}"
            for method in sorted(set(r.methods) - {"HEAD", "OPTIONS"}):
                yield method, prefix + r.path, name
