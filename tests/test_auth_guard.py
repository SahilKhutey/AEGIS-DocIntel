"""
Authentication-coverage regression tests.

The finding these lock in (verified by probing the live app anonymously):
    45 of 59 operations accepted requests with NO credentials — the legacy AEL routes,
    annotations, admin, advanced and webhook routers had never been wired to auth.
    An anonymous caller could export another tenant's document and wipe every document.

Invariant enforced here, for the whole app and for every future route:
    In production mode, any HTTP operation that is not explicitly public returns 401
    when called without credentials.
"""
from __future__ import annotations

import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth_guard import PUBLIC_PATHS, PUBLIC_PREFIXES, AuthGuardMiddleware, _is_public
from src.api.route_inspect import iter_operations
from src.main import app

DEV = {"Authorization": "Bearer dev-guard-test"}


def _fill(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "x", path)


@pytest.fixture()
def production(monkeypatch):
    """conftest defaults the suite to development mode; these tests need the real default."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "production")


@pytest.fixture()
def development(monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")


# ── The invariant ────────────────────────────────────────────────────────────

def test_every_non_public_operation_rejects_anonymous_requests(production):
    ops = sorted(set(iter_operations(app.routes)))
    assert len(ops) > 30, "route walker is broken (found too few operations)"

    leaked = []
    with TestClient(app, raise_server_exceptions=False) as c:
        for method, path, handler in ops:
            if _is_public(path, PUBLIC_PATHS, PUBLIC_PREFIXES):
                continue
            kwargs = {"json": {}} if method in ("POST", "PUT", "PATCH") else {}
            status = c.request(method, _fill(path), **kwargs).status_code
            if status != 401:
                leaked.append(f"{status} {method} {path}  ({handler})")
    assert not leaked, "Operations reachable WITHOUT credentials:\n  " + "\n  ".join(leaked)


def test_public_allowlist_is_minimal_and_explicit():
    # Changing this set is a security decision: it must show up in review as a test diff.
    assert PUBLIC_PATHS == frozenset(
        {"/health", "/health/live", "/health/ready", "/readiness", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}
    )
    assert PUBLIC_PREFIXES == ("/metrics",)


# ── Fail-closed for routes that do not exist yet ─────────────────────────────

def test_new_unprotected_route_is_protected_automatically(development):
    """The point of deny-by-default: a developer forgets Depends(get_current_tenant)."""
    mini = FastAPI()
    mini.add_middleware(AuthGuardMiddleware)

    @mini.get("/brand-new-forgot-auth")
    def forgot():  # no auth dependency whatsoever
        return {"secret": "data"}

    @mini.get("/health")
    def health():
        return {"ok": True}

    with TestClient(mini) as c:
        assert c.get("/brand-new-forgot-auth").status_code == 401
        assert c.get("/brand-new-forgot-auth", headers=DEV).status_code == 200
        assert c.get("/health").status_code == 200


# ── Path matching: public means exactly public ───────────────────────────────

@pytest.mark.parametrize(
    "path, expected",
    [
        ("/health", True),
        ("/health/", True),
        ("/readiness", True),
        ("/openapi.json", True),
        ("/metrics", True),
        ("/metrics/", True),
        ("/metrics/anything", True),
        ("/healthz", False),            # near-miss must NOT be public
        ("/healthcheck", False),
        ("/metricsx", False),           # prefix must respect the path boundary
        ("/metrics-private", False),
        ("/docs/../v1/documents", False),
        ("/v1/health", False),
        ("/", False),
        ("/v1/documents", False),
        ("/v1/admin/stats", False),
    ],
)
def test_public_path_matching(path, expected):
    assert _is_public(path, PUBLIC_PATHS, PUBLIC_PREFIXES) is expected


# ── Credential handling ──────────────────────────────────────────────────────

def test_dev_bypass_credentials_rejected_in_production(production):
    with TestClient(app, raise_server_exceptions=False) as c:
        assert c.get("/v1/documents", headers=DEV).status_code == 401
        assert c.get("/v1/documents", headers={"X-API-Key": "aegis-dev-key"}).status_code == 401
        assert c.get("/v1/admin/stats", headers=DEV).status_code == 401


def test_forged_and_malformed_credentials_rejected(development):
    with TestClient(app, raise_server_exceptions=False) as c:
        for headers in (
            {"Authorization": "Bearer eyJhbGciOiJub25lIn0.e30."},     # alg=none style
            {"Authorization": "Bearer "},
            {"Authorization": "Basic dXNlcjpwYXNz"},
            {"Authorization": "bearer"},
            {"X-API-Key": "not-a-real-key"},
        ):
            assert c.get("/v1/documents", headers=headers).status_code == 401, headers


def test_401_carries_www_authenticate(production):
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/v1/documents")
        assert r.status_code == 401
        assert r.headers.get("www-authenticate") == "Bearer"


def test_cors_preflight_is_not_blocked_by_the_guard(development):
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.options(
            "/v1/documents",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        assert r.status_code != 401  # CORSMiddleware answers preflights; credentials can't be sent


def test_websocket_scopes_pass_through_the_guard():
    """HTTP middleware cannot authenticate WebSockets; the route does (get_current_tenant_ws)."""
    import asyncio

    reached = []

    async def inner(scope, receive, send):
        reached.append(scope["type"])

    guard = AuthGuardMiddleware(inner)
    asyncio.run(guard({"type": "websocket", "path": "/v1/query/ws", "headers": []}, None, None))
    assert reached == ["websocket"]


# ── The original exploit, as a regression test ───────────────────────────────

def test_anonymous_cannot_read_or_wipe_another_tenants_document(development):
    victim = {"Authorization": "Bearer dev-victim-tenant"}
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.post(
            "/v1/ingest",
            headers=victim,
            files={"file": ("confidential.md", b"# Plan\n\nTarget: ACME Corp, price $41M.\n", "text/markdown")},
        )
        assert r.status_code == 201, r.text
        doc_id = r.json()["doc_id"]

        # attacker: no credentials at all
        leaked = c.get(f"/v1/documents/{doc_id}/export?format=markdown")
        assert leaked.status_code == 401
        assert "ACME" not in leaked.text
        assert c.delete("/v1/document").status_code == 401          # was: 204 + global wipe

        # victim's data is intact
        ok = c.get(f"/v1/documents/{doc_id}/export?format=markdown", headers=victim)
        assert ok.status_code == 200
        assert "ACME Corp" in ok.text
