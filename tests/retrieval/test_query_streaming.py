"""End-to-end SSE emission through the FastAPI router."""

from __future__ import annotations

import json
import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.config import get_settings
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_query_sse_emits_evidence_and_done(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AMDI_STORAGE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_QUEUE_BACKEND", "memory")
    monkeypatch.setenv("AMDI_ENABLE_RERANKER", "0")
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            store: InMemoryIndexStore = app.state.container.index_store()
            await store.add_units([
                CorpusUnit(unit_id="u1", document_id="d1", page=1,
                           bbox=(0, 0, 0.5, 0.1), section="body",
                           text="Quantum entanglement is central to modern physics.",
                           embedding=[1.0, 0.0]),
            ])

            async with c.stream(
                "POST", "/v1/query/", json={"raw": "quantum", "top_k": 3}
            ) as r:
                assert r.status_code == 200
                events = []
                async for line in r.aiter_lines():
                    if line.startswith("event:"):
                        events.append(line.split(":")[1].strip())

            assert events[0] == "start"
            assert "evidence" in events
            assert events[-1] == "done"
