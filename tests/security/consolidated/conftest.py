"""
Pytest configuration and fixtures for PROT-FINAL Consolidated Security Audit.
"""

from __future__ import annotations

import base64
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.app import app
from services.evaluation_gateway.audit import audit_service as gateway_audit_service
from services.evaluation_gateway.license_repository import license_repository
from services.evaluation_gateway.quotas import quota_manager
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.signing_key_registry import key_registry
from src.repositories.security_operations.audit_repository import audit_repository
from src.repositories.security_operations.incident_repository import incident_repository
from src.repositories.security_operations.security_event_repository import security_event_repository
from src.security.private_engine_guard import private_engine_guard
from src.services.security_operations.alert_evaluation_service import alert_evaluation_service


@pytest.fixture(autouse=True)
def clean_consolidated_environment():
    """Resets all gateway, licensing, device, session, quota, and operations stores."""
    activation_service.reset()
    gateway_audit_service.clear()
    key_registry.reset()
    license_repository.reset()
    revocation_registry.clear()
    quota_manager._usage.clear()
    with quota_manager.counter_repo._lock:
        quota_manager.counter_repo._counters.clear()
        quota_manager.counter_repo._id_index.clear()
    audit_repository.clear()
    incident_repository.clear()
    security_event_repository.clear()
    alert_evaluation_service.clear()
    private_engine_guard.reset()
    yield
    activation_service.reset()
    gateway_audit_service.clear()
    key_registry.reset()
    license_repository.reset()
    revocation_registry.clear()
    quota_manager._usage.clear()
    with quota_manager.counter_repo._lock:
        quota_manager.counter_repo._counters.clear()
        quota_manager.counter_repo._id_index.clear()
    audit_repository.clear()
    incident_repository.clear()
    security_event_repository.clear()
    alert_evaluation_service.clear()
    private_engine_guard.reset()


@pytest.fixture
def client():
    """Returns an isolated FastAPI TestClient for the evaluation gateway."""
    return TestClient(app)


@pytest.fixture
def keypair():
    """Generates a fresh in-memory Ed25519 keypair for client device simulation."""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    raw_pub = base64.b64encode(pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )).decode("ascii")
    return priv, pub, pem, raw_pub
