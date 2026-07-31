"""Retrieve → export → LLM-shaped prompt."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

from amdi.api.app import create_app
from amdi.security.auth import JWTIssuer


@pytest.mark.asyncio
async def test_export_holds_budget(monkeypatch, tmp_path) -> None:
    os.environ["AMDI_STORAGE_BACKEND"] = "filesystem"
    os.environ["AMDI_STORAGE_ROOT"] = str(tmp_path)
    os.environ["AMDI_QUEUE_BACKEND"] = "memory"
    os.environ["AMDI_JWT_SECRET"] = "test-secret-with-enough-entropy-1234"
    from amdi.config import get_settings
    get_settings.cache_clear()  # type: ignore[attr-defined]

    app = create_app()
    token = JWTIssuer().issue(user_id="alice", roles=("author",))

    evidence = [
        {"evidence_id": f"e{i}", "text": "x" * 400,
         "score_fused": 0.9 - i * 0.05,
         "citations": [{"document_id": "d.pdf", "page": i+1}]}
        for i in range(5)
    ]
    budgets = [128, 512, 2048, 8192]
    async with AsyncClient(transport=ASGITransport(app=app),
                            base_url="http://t") as c:
        async with app.router.lifespan_context(app):
            for fmt in ("markdown", "json", "jsonl"):
                for budget in budgets:
                    r = await c.post(
                        "/v1/export/llm-optimized",
                        json={"evidence": evidence, "fmt": fmt,
                              "budget": budget, "question": "q?"},
                        headers={"Authorization": f"Bearer {token}"})
                    assert r.status_code == 200, (fmt, budget, r.text)
                    used = r.json()["used_tokens"]
                    assert used <= budget, (fmt, budget, used)
