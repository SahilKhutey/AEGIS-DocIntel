"""
Pytest configuration and fixtures for PROT-04 Evaluation Security Tests.
"""

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.quotas import quota_manager
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.audit import audit_service
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token, CANONICAL_PRODUCT


@pytest.fixture(autouse=True)
def clean_evaluation_environment():
    """Ensures each test runs in an isolated and clean security state."""
    activation_service.reset()
    audit_service.clear()
    yield
    activation_service.reset()
    audit_service.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_eval_license():
    lic = issue_evaluation_license(
        user_id="sec-evaluator",
        duration_days=14,
        product=CANONICAL_PRODUCT,
    )
    token = export_license_token(lic)
    lic_id = lic["payload"]["license_id"]
    quota_manager.reset_usage(lic_id)
    return {
        "license_doc": lic,
        "token": token,
        "license_id": lic_id,
        "headers": {"X-Evaluation-License": token},
    }
