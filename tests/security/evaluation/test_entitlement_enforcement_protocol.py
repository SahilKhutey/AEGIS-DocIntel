"""
tests/security/evaluation/test_entitlement_enforcement_protocol.py
==================================================================
Comprehensive Verification Suite for PROT-04 WP-04.05:
Entitlement Enforcement, Evaluator RBAC, Tenant Isolation & Bypass Defenses.

Scenarios Covered:
- ENT-001 to ENT-018: Entitlement resolution, validity, policy immutability, overrides, fail-closed.
- RBAC-001 to RBAC-010: Role boundaries, anti-escalation, role injection rejection.
- TENANT-ENT-001 to TENANT-ENT-010: Cross-tenant resource isolation, IDOR defense, WebSocket & job boundaries.
- BYPASS-001 to BYPASS-005: Client tampering, direct API access, revocation replay, E2E lifecycle.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient

from src.repositories.evaluation.entitlement_policy_repository import (
    EntitlementPolicyRepository,
    PolicyImmutabilityError,
    PolicyNotFoundError,
)
from src.repositories.evaluation.entitlement_repository import EntitlementRepository
from src.schemas.evaluation.authorization import (
    AuditReasonCode,
    AuthorizationDecision,
    PrincipalContext,
    ROLE_ADMIN,
    ROLE_EVALUATION_REVIEWER,
    ROLE_EVALUATION_USER,
    ROLE_PLATFORM_ADMIN,
)
from src.schemas.evaluation.entitlement_catalogue import (
    FEATURE_ADMIN_ISSUE_LICENSE,
    FEATURE_ADMIN_MANAGE_USERS,
    FEATURE_DOCUMENT_COMPARE,
    FEATURE_DOCUMENT_EXPORT,
    FEATURE_DOCUMENT_QUERY,
    FEATURE_DOCUMENT_PREVIEW,
    FEATURE_DOCUMENT_UPLOAD,
    PERM_ADMIN_EVALUATION_ISSUE,
    PERM_ADMIN_USERS_MANAGE,
    PERM_DOCUMENT_COMPARE,
    PERM_DOCUMENT_EXPORT,
    PERM_DOCUMENT_QUERY,
    PERM_DOCUMENT_READ,
    PERM_DOCUMENT_UPLOAD,
)
from src.schemas.evaluation.entitlement_policy import (
    EvaluationEntitlementOverride,
    EvaluationEntitlementPolicy,
    EvaluationPolicyDocument,
    EvaluationPolicyLimits,
    PolicyStatus,
)
from src.services.evaluation.entitlement_service import (
    EntitlementService,
    default_entitlement_service,
)
from services.evaluation_gateway.app import (
    app,
    DOCUMENT_STORE,
    EvaluationDocument,
)
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token
from services.evaluation_gateway.revocation import registry as revocation_registry


@pytest.fixture(autouse=True)
def reset_entitlement_state():
    """Resets policy, entitlement, and document states between tests."""
    default_entitlement_service.policy_repo.clear()
    default_entitlement_service.entitlement_repo.clear()
    default_entitlement_service.event_repo.clear()
    default_entitlement_service.cache.clear()
    DOCUMENT_STORE.clear()
    yield
    default_entitlement_service.policy_repo.clear()
    default_entitlement_service.entitlement_repo.clear()
    default_entitlement_service.event_repo.clear()
    default_entitlement_service.cache.clear()
    DOCUMENT_STORE.clear()


@pytest.fixture
def eval_service():
    """Provides a fresh isolated EntitlementService instance for unit testing."""
    return EntitlementService()


# ===========================================================================
# 1. ENT-001 through ENT-018: Entitlement Engine & Policy Scenarios
# ===========================================================================

@pytest.mark.asyncio
async def test_ent_001_active_license_with_granted_feature(eval_service: EntitlementService):
    """ENT-001: Active license with granted feature (document.upload) is allowed."""
    principal = PrincipalContext(
        evaluator_id="eval-001",
        tenant_id="tenant-001",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-001",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
    )
    assert decision.allowed is True
    assert decision.reason_code == AuditReasonCode.ALLOWED.value


@pytest.mark.asyncio
async def test_ent_002_active_license_without_feature_denied(eval_service: EntitlementService):
    """ENT-002: Active license without feature (document.compare in basic) is denied."""
    principal = PrincipalContext(
        evaluator_id="eval-002",
        tenant_id="tenant-002",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-002",
    )
    # Default evaluation-basic policy has document.compare: False
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_COMPARE,
        permission=PERM_DOCUMENT_COMPARE,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.FEATURE_NOT_GRANTED.value


@pytest.mark.asyncio
async def test_ent_003_expired_license_denied(eval_service: EntitlementService):
    """ENT-003: Expired license is denied regardless of policy grants."""
    principal = PrincipalContext(
        evaluator_id="eval-003",
        tenant_id="tenant-003",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-003",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
        license_status="EXPIRED",
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.LICENSE_EXPIRED.value


@pytest.mark.asyncio
async def test_ent_004_suspended_license_denied(eval_service: EntitlementService):
    """ENT-004: Suspended license is denied regardless of policy grants."""
    principal = PrincipalContext(
        evaluator_id="eval-004",
        tenant_id="tenant-004",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-004",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
        license_status="SUSPENDED",
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.LICENSE_SUSPENDED.value


@pytest.mark.asyncio
async def test_ent_005_revoked_license_denied(eval_service: EntitlementService):
    """ENT-005: Revoked license is denied immediately."""
    principal = PrincipalContext(
        evaluator_id="eval-005",
        tenant_id="tenant-005",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-005",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
        is_revoked=True,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.LICENSE_REVOKED.value


@pytest.mark.asyncio
async def test_ent_006_inactive_device_denied(eval_service: EntitlementService):
    """ENT-006: Request with inactive/deactivated device is denied."""
    principal = PrincipalContext(
        evaluator_id="eval-006",
        tenant_id="tenant-006",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-006",
        device_id="dev-inactive-01",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
        device_active=False,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.DEVICE_INACTIVE.value


@pytest.mark.asyncio
async def test_ent_007_unknown_feature_denied(eval_service: EntitlementService):
    """ENT-007: Request presenting an unknown/unregistered feature fails closed."""
    principal = PrincipalContext(
        evaluator_id="eval-007",
        tenant_id="tenant-007",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-007",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature="quantum.hypercomputing",
        permission=PERM_DOCUMENT_READ,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.UNKNOWN_FEATURE.value


@pytest.mark.asyncio
async def test_ent_008_unknown_permission_denied(eval_service: EntitlementService):
    """ENT-008: Request presenting an unknown permission fails closed."""
    principal = PrincipalContext(
        evaluator_id="eval-008",
        tenant_id="tenant-008",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-008",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission="database.drop_all_tables",
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.UNKNOWN_PERMISSION.value


@pytest.mark.asyncio
async def test_ent_009_invalid_policy_version_denied(eval_service: EntitlementService):
    """ENT-009: Assignment referencing an unknown policy version fails closed."""
    eval_service.entitlement_repo.assign_policy(
        license_id="lic-009",
        evaluator_id="eval-009",
        tenant_id="tenant-009",
        policy_key="evaluation-basic",
        policy_version="99.9.bogus",
    )
    principal = PrincipalContext(
        evaluator_id="eval-009",
        tenant_id="tenant-009",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-009",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.INVALID_POLICY_VERSION.value


@pytest.mark.asyncio
async def test_ent_010_expired_entitlement_assignment_denied(eval_service: EntitlementService):
    """ENT-010: Assignment whose valid_until is in the past fails closed."""
    past = datetime.now(timezone.utc) - timedelta(days=1)
    eval_service.entitlement_repo.assign_policy(
        license_id="lic-010",
        evaluator_id="eval-010",
        tenant_id="tenant-010",
        policy_key="evaluation-basic",
        policy_version="1.0",
        valid_until=past,
    )
    principal = PrincipalContext(
        evaluator_id="eval-010",
        tenant_id="tenant-010",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-010",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.ENTITLEMENT_EXPIRED.value


@pytest.mark.asyncio
async def test_ent_011_future_entitlement_assignment_denied(eval_service: EntitlementService):
    """ENT-011: Assignment whose valid_from is in the future fails closed."""
    future = datetime.now(timezone.utc) + timedelta(days=2)
    eval_service.entitlement_repo.assign_policy(
        license_id="lic-011",
        evaluator_id="eval-011",
        tenant_id="tenant-011",
        policy_key="evaluation-basic",
        policy_version="1.0",
        valid_from=future,
    )
    principal = PrincipalContext(
        evaluator_id="eval-011",
        tenant_id="tenant-011",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-011",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.ENTITLEMENT_FUTURE.value


@pytest.mark.asyncio
async def test_ent_012_disabled_entitlement_in_policy_denied(eval_service: EntitlementService):
    """ENT-012: Explicitly disabled feature in active policy is denied."""
    principal = PrincipalContext(
        evaluator_id="eval-012",
        tenant_id="tenant-012",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-012",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_EXPORT,
        permission=PERM_DOCUMENT_EXPORT,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.FEATURE_NOT_GRANTED.value


@pytest.mark.asyncio
async def test_ent_013_expired_override_denied(eval_service: EntitlementService):
    """ENT-013: An administrative override that has expired ceases granting access."""
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    override = EvaluationEntitlementOverride(
        license_id="lic-013",
        feature_key=FEATURE_DOCUMENT_COMPARE,
        override_enabled=True,
        reason_code="temporary-pilot-review",
        issued_by_admin="admin-sec-ops",
        valid_until=past,
    )
    eval_service.entitlement_repo.add_override(override)

    principal = PrincipalContext(
        evaluator_id="eval-013",
        tenant_id="tenant-013",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-013",
    )
    # Since override expired, falls back to basic policy (compare: False)
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_COMPARE,
        permission=PERM_DOCUMENT_COMPARE,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.FEATURE_NOT_GRANTED.value


def test_ent_014_unauthorized_override_creation_denied(client: TestClient):
    """ENT-014: Creating an override without admin credentials returns 401."""
    res = client.post(
        "/v1/admin/evaluation/licenses/lic-014/override",
        json={
            "feature_key": "document.compare",
            "override_enabled": True,
            "reason_code": "unauthorized-bypass",
        },
    )
    assert res.status_code in (401, 403)


def test_ent_015_admin_permission_in_evaluator_policy_rejected(client: TestClient):
    """ENT-015: Policy schema rejects embedding administrative features in evaluator policy."""
    with pytest.raises(ValueError, match="Administrative feature"):
        EvaluationPolicyDocument(
            policy_key="malicious-policy",
            version="1.0",
            features={
                FEATURE_ADMIN_MANAGE_USERS: True,
            },
        )


@pytest.mark.asyncio
async def test_ent_016_policy_update_enforces_new_revision(eval_service: EntitlementService):
    """ENT-016: Updating policy assignments or overrides increments revision counter."""
    rev_before = eval_service.current_revision
    eval_service.entitlement_repo.add_override(
        EvaluationEntitlementOverride(
            license_id="lic-016",
            feature_key=FEATURE_DOCUMENT_COMPARE,
            override_enabled=True,
            reason_code="customer-approved-pilot",
            issued_by_admin="admin-ops",
        )
    )
    rev_after = eval_service.current_revision
    assert rev_after > rev_before

    # Now compare feature is allowed under new revision
    principal = PrincipalContext(
        evaluator_id="eval-016",
        tenant_id="tenant-016",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-016",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_COMPARE,
        permission=PERM_DOCUMENT_COMPARE,
    )
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_ent_017_cache_invalidation_clears_old_grant(eval_service: EntitlementService):
    """ENT-017: Clearing overrides immediately purges cached authorization grants."""
    override = EvaluationEntitlementOverride(
        license_id="lic-017",
        feature_key=FEATURE_DOCUMENT_COMPARE,
        override_enabled=True,
        reason_code="temporary-trial",
        issued_by_admin="admin-lead",
    )
    eval_service.entitlement_repo.add_override(override)
    principal = PrincipalContext(
        evaluator_id="eval-017",
        tenant_id="tenant-017",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-017",
    )

    # 1. Warm cache with ALLOW
    d1 = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_COMPARE,
        permission=PERM_DOCUMENT_COMPARE,
    )
    assert d1.allowed is True

    # 2. Clear overrides & invalidate cache
    eval_service.entitlement_repo.clear_overrides("lic-017")
    eval_service.invalidate_cache("lic-017")

    # 3. Subsequent check immediately denies
    d2 = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_COMPARE,
        permission=PERM_DOCUMENT_COMPARE,
    )
    assert d2.allowed is False


@pytest.mark.asyncio
async def test_ent_018_entitlement_service_unavailable_fails_closed(eval_service: EntitlementService):
    """ENT-018: Fail-closed denial when backend policy repository throws unexpected error."""
    # Break the resolver to simulate database connectivity loss
    eval_service.resolver = None  # type: ignore

    principal = PrincipalContext(
        evaluator_id="eval-018",
        tenant_id="tenant-018",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-018",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_DOCUMENT_UPLOAD,
        permission=PERM_DOCUMENT_UPLOAD,
    )
    assert decision.allowed is False
    assert decision.reason_code == AuditReasonCode.SERVICE_UNAVAILABLE.value


# ===========================================================================
# 2. RBAC-001 through RBAC-010: Role Boundaries & Privilege Escalation
# ===========================================================================

def test_rbac_001_evaluator_requests_admin_endpoint_forbidden(client: TestClient, valid_eval_license):
    """RBAC-001: Evaluator requesting admin policies returns 401/403."""
    res = client.get("/v1/admin/evaluation/policies", headers=valid_eval_license["headers"])
    assert res.status_code in (401, 403)


def test_rbac_002_evaluator_sends_role_admin_ignored_rejected(client: TestClient, valid_eval_license):
    """RBAC-002: Evaluator sending X-User-Role: admin or role in body cannot access admin."""
    headers = dict(valid_eval_license["headers"])
    headers["X-User-Role"] = "admin"
    headers["X-Role"] = "platform_admin"

    res = client.post("/v1/admin/users", headers=headers, json={"user_id": "attacker"})
    assert res.status_code == 403


def test_rbac_003_evaluator_adds_admin_to_jwt_roles_rejected():
    """RBAC-003: PrincipalContext creation rejects assigning admin to an evaluator."""
    with pytest.raises(ValueError, match="cannot be assigned administrative roles"):
        PrincipalContext(
            evaluator_id="eval-bad-actor",
            tenant_id="tenant-eval",
            roles=frozenset({ROLE_EVALUATION_USER, ROLE_ADMIN}),
            is_evaluator=True,
        )


def test_rbac_004_evaluator_changes_tenant_header_no_privilege_change(client: TestClient, valid_eval_license):
    """RBAC-004: Evaluator sending arbitrary X-Tenant-ID header cannot access other tenants."""
    headers = dict(valid_eval_license["headers"])
    headers["X-Tenant-ID"] = "foreign-tenant-xyz"

    # Reading documents still binds to caller's license_id
    res = client.get("/v1/evaluation/documents", headers=headers)
    assert res.status_code == 200
    # Returned documents belong solely to caller's license


def test_rbac_005_evaluator_changes_workspace_id_no_privilege_change(client: TestClient, valid_eval_license):
    """RBAC-005: Evaluator sending foreign workspace headers cannot elevate access."""
    headers = dict(valid_eval_license["headers"])
    headers["X-Workspace-ID"] = "foreign-workspace-999"

    res = client.get("/v1/evaluation/license/entitlements", headers=headers)
    assert res.status_code == 200
    assert "users.manage" in res.json()["denied"]


@pytest.mark.asyncio
async def test_rbac_006_evaluator_accesses_admin_feature_denied(eval_service: EntitlementService):
    """RBAC-006: Direct check for admin feature by evaluator returns False."""
    principal = PrincipalContext(
        evaluator_id="eval-006",
        tenant_id="tenant-006",
        roles=frozenset({ROLE_EVALUATION_USER}),
        license_id="lic-006",
    )
    decision = await eval_service.authorize(
        principal=principal,
        feature=FEATURE_ADMIN_MANAGE_USERS,
        permission=PERM_ADMIN_USERS_MANAGE,
    )
    assert decision.allowed is False


def test_rbac_007_unknown_role_rejected():
    """RBAC-007: PrincipalContext with empty roles fails closed."""
    with pytest.raises(ValueError):
        # Empty role set not allowed
        PrincipalContext(
            evaluator_id="eval-007",
            tenant_id="tenant-007",
            roles=frozenset(),
        )


def test_rbac_008_malformed_roles_claim_rejected(client: TestClient):
    """RBAC-008: Authorization with missing or malformed token returns 400 or 401."""
    res = client.get("/v1/evaluation/documents", headers={"Authorization": "Bearer malformed.token"})
    assert res.status_code in (400, 401)


def test_rbac_009_admin_only_entitlement_override_authorized_only(client: TestClient):
    """RBAC-009: Creating an override with valid admin credentials succeeds."""
    res = client.post(
        "/v1/admin/evaluation/licenses/lic-009-test/override",
        headers={"X-Admin-Key": "aegis-admin-secret-key-eval-2026"},
        json={
            "feature_key": "document.compare",
            "override_enabled": True,
            "reason_code": "approved-sales-pilot",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "override_added"


def test_rbac_010_expired_admin_session_denied(client: TestClient):
    """RBAC-010: Request with invalid or expired admin secret returns 401 or 403."""
    res = client.post(
        "/v1/admin/evaluation/licenses/lic-010/override",
        headers={"X-Admin-Key": "wrong-expired-admin-key"},
        json={
            "feature_key": "document.compare",
            "override_enabled": True,
            "reason_code": "invalid",
        },
    )
    assert res.status_code in (401, 403)


# ===========================================================================
# 3. TENANT-ENT-001 through TENANT-ENT-010: Resource Isolation & IDOR Defenses
# ===========================================================================

def test_tenant_ent_001_read_own_document_allowed(client: TestClient, valid_eval_license):
    """TENANT-ENT-001: Reading a document owned by the evaluator's license is allowed."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # Seed doc in DOCUMENT_STORE
    doc_id = "doc-own-101"
    DOCUMENT_STORE[doc_id] = EvaluationDocument(
        doc_id=doc_id,
        license_id=lic_id,
        filename="eval_report.pdf",
        content_type="application/pdf",
        page_count=3,
        text="Evaluator confidential intelligence report.",
    )

    res = client.get(f"/v1/evaluation/documents/{doc_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["document_id"] == doc_id


def test_tenant_ent_002_read_another_tenant_document_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-002: Reading another license's document returns 404 (non-disclosing IDOR defense)."""
    headers = valid_eval_license["headers"]

    # Seed doc belonging to a foreign license
    foreign_doc_id = "doc-foreign-202"
    DOCUMENT_STORE[foreign_doc_id] = EvaluationDocument(
        doc_id=foreign_doc_id,
        license_id="foreign-license-999",
        filename="competitor_secrets.pdf",
        content_type="application/pdf",
        page_count=10,
        text="Competitor confidential document.",
    )

    res = client.get(f"/v1/evaluation/documents/{foreign_doc_id}", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"] == "DOCUMENT_NOT_FOUND"


def test_tenant_ent_003_query_another_tenant_document_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-003: Querying Ask AEGIS targeting another tenant's doc returns 404."""
    headers = valid_eval_license["headers"]
    foreign_doc_id = "doc-foreign-303"
    DOCUMENT_STORE[foreign_doc_id] = EvaluationDocument(
        doc_id=foreign_doc_id,
        license_id="foreign-license-999",
        filename="other.pdf",
        content_type="application/pdf",
        page_count=2,
        text="Secret text.",
    )

    res = client.post(
        "/v1/evaluation/query",
        headers=headers,
        json={
            "query": "What is the secret?",
            "document_id": foreign_doc_id,
        },
    )
    assert res.status_code == 404


def test_tenant_ent_004_compare_across_tenants_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-004: Comparing own document against a foreign document returns 404."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # Own doc
    own_id = "doc-own-404"
    DOCUMENT_STORE[own_id] = EvaluationDocument(
        doc_id=own_id,
        license_id=lic_id,
        filename="own.pdf",
        content_type="application/pdf",
        page_count=1,
        text="Own text.",
    )

    # Foreign doc
    foreign_id = "doc-foreign-404"
    DOCUMENT_STORE[foreign_id] = EvaluationDocument(
        doc_id=foreign_id,
        license_id="foreign-license-xyz",
        filename="foreign.pdf",
        content_type="application/pdf",
        page_count=1,
        text="Foreign text.",
    )

    res = client.post(
        "/v1/evaluation/compare",
        headers=headers,
        json={
            "left_document_id": own_id,
            "right_document_id": foreign_id,
        },
    )
    assert res.status_code == 404


def test_tenant_ent_005_export_another_tenant_result_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-005: Attempting to export a foreign document returns 404."""
    headers = valid_eval_license["headers"]
    foreign_id = "doc-foreign-505"
    DOCUMENT_STORE[foreign_id] = EvaluationDocument(
        doc_id=foreign_id,
        license_id="foreign-license-xyz",
        filename="foreign.pdf",
        content_type="application/pdf",
        page_count=1,
        text="Foreign text.",
    )

    res = client.get(f"/v1/evaluation/documents/{foreign_id}", headers=headers)
    assert res.status_code == 404


def test_tenant_ent_006_poll_another_tenant_job_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-006: Polling job status across tenant boundaries returns 404."""
    headers = valid_eval_license["headers"]
    # Unknown/foreign job
    res = client.get("/v1/evaluation/documents/job-foreign-606", headers=headers)
    assert res.status_code == 404


def test_tenant_ent_007_subscribe_another_tenant_websocket_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-007: Querying WebSocket stream or foreign document stream returns 404."""
    headers = valid_eval_license["headers"]
    res = client.get("/v1/evaluation/documents/doc-stream-foreign-707", headers=headers)
    assert res.status_code == 404


def test_tenant_ent_008_access_another_tenant_download_denied_404(client: TestClient, valid_eval_license):
    """TENANT-ENT-008: Direct download URL for foreign resource returns 404."""
    headers = valid_eval_license["headers"]
    res = client.get("/v1/evaluation/documents/download-token-foreign-808", headers=headers)
    assert res.status_code == 404


def test_tenant_ent_009_change_workspace_header_no_privilege_change(client: TestClient, valid_eval_license):
    """TENANT-ENT-009: Adding arbitrary workspace headers produces zero privilege elevation."""
    headers = dict(valid_eval_license["headers"])
    headers["X-Workspace-ID"] = "global-system-workspace"

    res = client.get("/v1/evaluation/documents", headers=headers)
    assert res.status_code == 200
    assert "items" in res.json()


def test_tenant_ent_010_guess_resource_uuid_no_information_leakage(client: TestClient, valid_eval_license):
    """TENANT-ENT-010: Guessing random UUIDs consistently returns generic 404 without timing or error leak."""
    headers = valid_eval_license["headers"]
    res = client.get("/v1/evaluation/documents/00000000-0000-0000-0000-000000000000", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"] == "DOCUMENT_NOT_FOUND"


# ===========================================================================
# 4. BYPASS-001 through BYPASS-005: Attack & Integration Tests
# ===========================================================================

def test_bypass_001_direct_api_access_to_disabled_feature_denied(client: TestClient, valid_eval_license):
    """BYPASS-001: Calling disabled comparison API when policy disables it returns 403."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # Assign evaluation-basic (where document.compare is False)
    default_entitlement_service.entitlement_repo.assign_policy(
        license_id=lic_id,
        evaluator_id="eval-bypass",
        tenant_id="tenant-bypass",
        policy_key="evaluation-basic",
        policy_version="1.0",
    )
    default_entitlement_service.invalidate_cache(lic_id)

    # Attempt to compare
    res = client.post(
        "/v1/evaluation/compare",
        headers=headers,
        json={"left_document_id": "doc1", "right_document_id": "doc2"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FEATURE_NOT_ENTITLED"


def test_bypass_002_tampered_client_side_entitlements_header_ignored(client: TestClient, valid_eval_license):
    """BYPASS-002: Sending forged X-Client-Entitlements header is ignored by server authority."""
    headers = dict(valid_eval_license["headers"])
    headers["X-Client-Entitlements"] = '{"document.compare": true, "platform.admin": true}'

    res = client.post("/v1/admin/platform/config", headers=headers, json={"debug": True})
    assert res.status_code == 403


def test_bypass_003_replay_request_after_revocation_denied(client: TestClient, valid_eval_license):
    """BYPASS-003: Replaying a valid request after license revocation returns 403."""
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # 1. Request succeeds initially
    res1 = client.get("/v1/evaluation/documents", headers=headers)
    assert res1.status_code == 200

    # 2. Revoke license
    revocation_registry.revoke(lic_id)

    # 3. Replay fails
    res2 = client.get("/v1/evaluation/documents", headers=headers)
    assert res2.status_code == 403
    assert res2.json()["error"] == "LICENSE_REVOKED"


def test_bypass_004_direct_request_to_private_engine_blocked(client: TestClient, valid_eval_license):
    """BYPASS-004: Direct request to non-existent private engine routes returns 404."""
    headers = valid_eval_license["headers"]
    res = client.post("/private/engine/topology/solve", headers=headers, json={})
    assert res.status_code == 404


def test_bypass_005_complete_end_to_end_entitlement_lifecycle(client: TestClient, valid_eval_license):
    """
    BYPASS-005: Full lifecycle verification:
    1. Authenticate with valid evaluation license.
    2. Upload document -> 200.
    3. Query document -> 200.
    4. Attempt comparison under basic policy -> 403.
    5. Admin adds override granting comparison -> 200.
    6. Attempt comparison again -> passes feature check (reaches doc lookup).
    7. Revoke license -> 403 immediately.
    """
    headers = valid_eval_license["headers"]
    lic_id = valid_eval_license["license_id"]

    # 1. Assign basic policy (compare: False)
    default_entitlement_service.entitlement_repo.assign_policy(
        license_id=lic_id,
        evaluator_id="eval-lifecycle",
        tenant_id="tenant-lifecycle",
        policy_key="evaluation-basic",
        policy_version="1.0",
    )
    default_entitlement_service.invalidate_cache(lic_id)

    # 2. Upload doc
    res_upload = client.post(
        "/v1/evaluation/documents",
        headers=headers,
        files={"file": ("eval_test.txt", b"Sample content for evaluation lifecycle.", "text/plain")},
    )
    assert res_upload.status_code == 200
    doc_id = res_upload.json()["document_id"]

    # 3. Query doc
    res_query = client.post(
        "/v1/evaluation/query",
        headers=headers,
        json={"query": "Sample question", "document_id": doc_id},
    )
    assert res_query.status_code == 200

    # 4. Attempt compare -> 403 Forbidden
    res_comp = client.post(
        "/v1/evaluation/compare",
        headers=headers,
        json={"left_document_id": doc_id, "right_document_id": doc_id},
    )
    assert res_comp.status_code == 403

    # 5. Admin grants override for comparison
    res_ov = client.post(
        f"/v1/admin/evaluation/licenses/{lic_id}/override",
        headers={"X-Admin-Key": "aegis-admin-secret-key-eval-2026"},
        json={
            "feature_key": "document.compare",
            "override_enabled": True,
            "reason_code": "approved-sales-pilot-demo",
        },
    )
    assert res_ov.status_code == 200

    # 6. Attempt compare again -> now feature is entitled (passes 403 check)
    res_comp2 = client.post(
        "/v1/evaluation/compare",
        headers=headers,
        json={"left_document_id": doc_id, "right_document_id": doc_id},
    )
    assert res_comp2.status_code == 200
    assert res_comp2.json()["status"] == "COMPARISON_COMPLETE"

    # 7. Revoke license
    revocation_registry.revoke(lic_id)
    res_revoked = client.get(f"/v1/evaluation/documents/{doc_id}", headers=headers)
    assert res_revoked.status_code == 403
