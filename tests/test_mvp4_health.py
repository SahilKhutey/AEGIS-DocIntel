"""
tests/test_mvp4_health.py
=========================
Unit and integration tests for liveness and readiness endpoints and HealthService.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.health import router as health_router
from src.services.health_service import HealthService


class MockHealthyContainer:
    async def verify_readiness(self):
        return True, {"database": "ok", "memory": "ok", "container": "ok"}


class MockDegradedContainer:
    async def verify_readiness(self):
        return False, {"database": "unhealthy: connection failed", "memory": "ok", "container": "ok"}


def test_liveness_returns_ok():
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)

    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_readiness_healthy_container():
    app = FastAPI()
    app.include_router(health_router)
    app.state.container = MockHealthyContainer()
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["dependencies"]["database"] == "ok"


def test_readiness_unhealthy_container_fails_non_disclosing():
    app = FastAPI()
    app.include_router(health_router)
    app.state.container = MockDegradedContainer()
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["database"] == "unavailable"
    # Ensure internal exception details are NOT leaked to caller
    assert "connection failed" not in resp.text


def test_readiness_missing_container_fails_safe():
    app = FastAPI()
    app.include_router(health_router)
    app.state.container = None
    client = TestClient(app)

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["dependencies"]["database"] == "unavailable"
