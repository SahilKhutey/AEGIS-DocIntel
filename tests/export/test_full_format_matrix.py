"""Each of the three exporters round-trips through the API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", ["markdown", "json", "jsonl"])
async def test_export_endpoint_returns_body(fmt: str, monkeypatch, tmp_path) -> None:
    import os
    os.environ["AMDI_STORAGE_BACKEND"] = "memory"
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    os.environ["AMDI_JWT_SECRET"] = "test-secret-with-enough-entropy-1234"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    token = _token()
    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            r = await c.post(
                "/v1/export/llm-optimized",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "evidence": [
                        {"evidence_id": "e1", "text": "alpha",
                         "score_fused": 0.9,
                         "citations": [{"document_id": "d.pdf", "page": 1}]},
                    ],
                    "fmt": fmt, "budget": 800, "question": "q",
                },
            )
    assert r.status_code == 200, (fmt, r.text)
    payload = r.json()
    assert payload["fmt"] == fmt or (
        fmt == "markdown" and payload["fmt"] in ("markdown", "md")
    )
    assert payload["used_tokens"] <= payload["budget"]


def _token() -> str:
    from amdi.security.auth import JWTIssuer
    return JWTIssuer().issue(
        user_id="alice", roles=("admin",),
        scopes=("doc:read", "query:run", "export:build", "admin:audit"),
    )
