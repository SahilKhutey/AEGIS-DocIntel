"""
tests.security.authorization.test_authorization_suite
====================================================
Tests for WP-07.01 Authorization & RBAC Security Gate (RBAC-001 through RBAC-010).
"""

import pytest
from aegis.security.auth import Authorizer, AuthBenchmarkRunner


@pytest.fixture
def authorizer():
    return Authorizer()


def test_rbac_001_viewer_denied_admin_endpoint(authorizer):
    ok, code, reason = authorizer.authorize("u1", "t1", {"viewer"}, "manage_tenant_users")
    assert not ok
    assert code == 403


def test_rbac_002_user_denied_other_user_record_modification(authorizer):
    ok, code, _ = authorizer.authorize(
        "u1", "t1", {"viewer"}, "delete_own_documents",
        resource_id="doc-1", resource_tenant_id="t1", resource_owner_id="u2"
    )
    assert not ok
    assert code in (403, 404)


def test_rbac_003_analyst_permitted_analysis(authorizer):
    ok, code, _ = authorizer.authorize("u1", "t1", {"editor"}, "run_document_analysis")
    assert ok
    assert code == 200


def test_rbac_004_payload_privilege_escalation_blocked(authorizer):
    ok, code, reason = authorizer.authorize(
        "u1", "t1", {"viewer"}, "view_own_documents",
        client_payload={"role": "admin", "is_admin": True}
    )
    assert not ok
    assert code == 403
    assert "escalation" in reason.lower()


def test_rbac_005_anti_idor_cross_tenant_resource_returns_404(authorizer):
    # Cross tenant resource returns 404 to avoid disclosing resource existence
    ok, code, _ = authorizer.authorize(
        "u1", "tenant-a", {"viewer"}, "view_own_documents",
        resource_id="doc-secret", resource_tenant_id="tenant-b"
    )
    assert not ok
    assert code == 404


def test_rbac_006_unauthorized_audit_logs_blocked(authorizer):
    ok, code, _ = authorizer.authorize("u1", "t1", {"viewer"}, "view_tenant_audit_logs")
    assert not ok
    assert code == 403


def test_rbac_007_scoped_api_key_permission_limit(authorizer):
    ok, code, _ = authorizer.authorize("key-1", "t1", {"viewer"}, "upload_documents")
    assert not ok
    assert code == 403


def test_rbac_008_unauthenticated_request_fails_closed(authorizer):
    ok, code, _ = authorizer.authorize("", "", set(), "upload_documents")
    assert not ok
    assert code == 403


def test_rbac_009_unmapped_action_denied_by_default(authorizer):
    ok, code, _ = authorizer.authorize("u1", "t1", {"tenant_admin"}, "unregistered_dangerous_action")
    assert not ok
    assert code == 403


def test_rbac_010_benchmark_runner_full_suite():
    runner = AuthBenchmarkRunner()
    report = runner.run_authorization_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 10
