"""
Pytest configuration and fixtures for PROT-04 WP-04.08 Security Operations Tests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.app import app
from services.evaluation_gateway.license_repository import license_repository
from services.evaluation_gateway.quotas import quota_manager
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.signing_key_registry import key_registry


@pytest.fixture
def client():
    """Provides a TestClient initialized with clean evaluation gateway state."""
    activation_service.reset()
    key_registry.reset()
    license_repository.reset()
    revocation_registry.clear()
    return TestClient(app)
