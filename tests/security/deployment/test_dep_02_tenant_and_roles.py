"""
Tests for PROT-FINAL-05: Tenant Isolation & Database Role Boundaries
Covers DEP-TEST-005, DEP-TEST-006
"""

import pytest

from src.gateway.request_validation import request_validator
from src.repositories.tenant_scoped import (
    TenantScopedRepository,
    DatabaseSecurityViolation,
)


def test_dep_005_untrusted_tenant_header_ignored_and_sanitized():
    """DEP-TEST-005: Client cannot spoof or override tenant boundary via untrusted headers."""
    authenticated_tenant = "tenant-legitimate-100"
    
    # Client attempts to spoof another tenant via X-Tenant-ID header
    client_headers = {
        "x-tenant-id": "tenant-victim-200",
        "authorization": "Bearer dummy_token",
    }
    
    resolved_tenant = request_validator.sanitize_tenant_context(
        headers=client_headers,
        authenticated_tenant_id=authenticated_tenant,
    )
    # Server strictly enforces authenticated tenant
    assert resolved_tenant == authenticated_tenant
    assert resolved_tenant != "tenant-victim-200"


def test_dep_006_database_role_escalation_denied():
    """DEP-TEST-006: Application database role (aegis_app) cannot execute DDL or escalate privileges."""
    repo = TenantScopedRepository(current_role="aegis_app")

    # DML is permitted
    dml_res = repo.execute_raw_sql("SELECT * FROM documents WHERE tenant_id = :tenant_id")
    assert dml_res[0]["status"] == "EXECUTED"

    # DDL statements must be blocked
    with pytest.raises(DatabaseSecurityViolation, match="role 'aegis_app' cannot execute DDL"):
        repo.execute_raw_sql("DROP TABLE identity_evaluators CASCADE")

    with pytest.raises(DatabaseSecurityViolation, match="role 'aegis_app' cannot execute DDL"):
        repo.execute_raw_sql("ALTER TABLE usage_reservations ADD COLUMN backdoor TEXT")

    with pytest.raises(DatabaseSecurityViolation, match="role 'aegis_app' cannot execute DDL"):
        repo.execute_raw_sql("CREATE ROLE superuser_backdoor SUPERUSER")


def test_tenant_data_isolation():
    """Verifies that queries enforce tenant boundaries and prevent cross-tenant access."""
    repo = TenantScopedRepository(current_role="aegis_app")
    repo.clear()

    # Save document for Tenant A
    repo.save_document(tenant_id="tenant-A", document_id="doc-1", data={"title": "Secret A"})

    # Save document for Tenant B
    repo.save_document(tenant_id="tenant-B", document_id="doc-2", data={"title": "Secret B"})

    # Tenant A cannot see Tenant B's document
    doc_b_from_a = repo.get_document(tenant_id="tenant-A", document_id="doc-2")
    assert doc_b_from_a is None

    # Tenant A list documents only returns Tenant A documents
    docs_a = repo.list_documents(tenant_id="tenant-A")
    assert len(docs_a) == 1
    assert docs_a[0]["title"] == "Secret A"
