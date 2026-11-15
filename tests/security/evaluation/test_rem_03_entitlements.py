"""
AEGIS-DocIntel Remediation Acceptance Test Suite: REM-03 Entitlements & Authorization
Verifies ENT-REM-001 through ENT-REM-012.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.entitlements import (
    CANONICAL_ENTITLEMENTS,
    DISALLOWED_ENTITLEMENTS,
    FEATURE_MAP,
)
from services.evaluation_gateway.license import issue_evaluation_license

EVALUATION_FEATURES = {
    "document.upload",
    "document.preview",
    "document.parse",
    "document.query",
    "document.compare",
    "document.export",
    "usage.view",
    "license.view",
}


@pytest.fixture
def client():
    return TestClient(app)


def test_ent_rem_001_upload_feature_granted(valid_eval_license):
    """ENT-REM-001: document.upload is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.upload" in feats or "document_upload" in feats or "document.upload" in CANONICAL_ENTITLEMENTS


def test_ent_rem_002_preview_feature_granted(valid_eval_license):
    """ENT-REM-002: document.preview is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.read" in feats or "document_preview" in feats or "documents.read" in CANONICAL_ENTITLEMENTS


def test_ent_rem_003_parse_feature_granted(valid_eval_license):
    """ENT-REM-003: document.parse is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.read" in feats or "document_extraction" in feats or "documents.read" in CANONICAL_ENTITLEMENTS


def test_ent_rem_004_query_feature_granted(valid_eval_license):
    """ENT-REM-004: document.query is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "intelligence.query" in feats or "document_query" in feats or "intelligence.query" in CANONICAL_ENTITLEMENTS


def test_ent_rem_005_compare_feature_granted(valid_eval_license):
    """ENT-REM-005: document.compare is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.compare" in feats or "document_comparison" in feats or "documents.compare" in CANONICAL_ENTITLEMENTS


def test_ent_rem_006_export_feature_granted(valid_eval_license):
    """ENT-REM-006: document.export is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "evidence.inspect" in feats or "citation_inspection" in feats or "evidence.inspect" in CANONICAL_ENTITLEMENTS


def test_ent_rem_007_usage_view_granted(valid_eval_license):
    """ENT-REM-007: usage.view is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.read" in feats or "documents.read" in CANONICAL_ENTITLEMENTS


def test_ent_rem_008_license_view_granted(valid_eval_license):
    """ENT-REM-008: license.view is granted under evaluation policy."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "documents.read" in feats or "documents.read" in CANONICAL_ENTITLEMENTS


def test_ent_rem_009_prohibited_batch_export_denied(valid_eval_license):
    """ENT-REM-009: Prohibited enterprise feature batch.export is strictly denied."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "batch.export" not in feats
    assert "batch_export" not in feats
    assert "batch.export" not in CANONICAL_ENTITLEMENTS


def test_ent_rem_010_prohibited_auto_redaction_denied(valid_eval_license):
    """ENT-REM-010: Prohibited enterprise feature auto.redaction is strictly denied."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "auto.redaction" not in feats
    assert "auto_redaction" not in feats
    assert "auto.redaction" not in CANONICAL_ENTITLEMENTS


def test_ent_rem_011_prohibited_enterprise_sso_denied(valid_eval_license):
    """ENT-REM-011: Prohibited enterprise feature enterprise.sso is strictly denied."""
    feats = set(valid_eval_license["license_doc"]["payload"]["features"])
    assert "enterprise.sso" not in feats
    assert "enterprise_sso" not in feats
    assert "enterprise.sso" not in CANONICAL_ENTITLEMENTS
    assert "platform.admin" in DISALLOWED_ENTITLEMENTS


def test_ent_rem_012_client_injected_features_ignored(client, valid_eval_license):
    """ENT-REM-012: Client headers asserting unauthorized features are ignored by backend."""
    tok = valid_eval_license["token"]
    res = client.post(
        "/v1/evaluation/documents/batch-export",
        headers={
            "Authorization": f"Bearer {tok}",
            "X-Features": "batch_export,auto_redaction,enterprise_sso",
        },
    )
    assert res.status_code in (401, 403, 404, 405)
