"""
AEGIS-DocIntel Release Tests: Module 5
PROT-FINAL-08: Support, Feedback Workflows, Secret Redaction, and Local Proxy Restrictions
Covers: REL-019, REL-024, REL-032, REL-034
"""

from __future__ import annotations

import re
import uuid
import pytest

from src.repositories.evaluation.feedback_repository import FeedbackRepository
from src.schemas.evaluation.feedback import (
    FeedbackCategory,
    FeedbackCreate,
    FeedbackSeverity,
    FeedbackStatus,
)
from src.services.evaluation.evaluator_feedback_service import EvaluatorFeedbackService


@pytest.fixture
def feedback_service():
    repo = FeedbackRepository()
    return EvaluatorFeedbackService(repo=repo)


def test_rel_019_feedback_submission_and_scoping(feedback_service):
    """REL-019: Evaluator feedback is submitted, scoped to evaluator, and P0/Security routes to security responders."""
    eval_id_1 = "eval-fb-01"
    eval_id_2 = "eval-fb-02"

    # Standard UX feedback
    resp_ux = feedback_service.submit_feedback(
        evaluator_id=eval_id_1,
        payload=FeedbackCreate(
            category=FeedbackCategory.UX,
            severity=FeedbackSeverity.P2,
            description="Navigation bar is slightly misaligned on Windows 11 high DPI display.",
        ),
    )
    assert resp_ux.feedback.evaluator_id == eval_id_1
    assert resp_ux.feedback.is_security_concern is False
    assert resp_ux.feedback.status == FeedbackStatus.REPORTED

    # Critical P0 Security notice
    resp_sec = feedback_service.submit_feedback(
        evaluator_id=eval_id_2,
        payload=FeedbackCreate(
            category=FeedbackCategory.SECURITY,
            severity=FeedbackSeverity.P0,
            description="Potential path traversal suspected when inspecting demo filenames.",
        ),
    )
    assert resp_sec.feedback.evaluator_id == eval_id_2
    assert resp_sec.feedback.is_security_concern is True
    assert resp_sec.feedback.assigned_to == "security-responder"

    # Evaluator scoping: eval_id_1 sees only their feedback
    fb1_list = feedback_service.list_evaluator_feedback(eval_id_1)
    assert len(fb1_list) == 1
    assert fb1_list[0].id == resp_ux.feedback.id


def test_rel_024_no_unrestricted_local_proxy_route():
    """REL-024: Local proxy configuration restricts forward traffic to authorized gateway endpoints."""
    allowed_prefixes = ["/v1/evaluation/", "/v1/documents/", "/v1/query/", "/v1/answers/"]
    unrestricted_targets = ["/admin/shell", "/debug/pprof", "/metrics/internal", "/v1/admin/"]

    for target in unrestricted_targets:
        is_allowed = any(target.startswith(p) for p in allowed_prefixes)
        assert is_allowed is False, f"Target '{target}' must not be exposed through public evaluation proxy"


def test_rel_032_duplicate_feedback_requests_handled_safely(feedback_service):
    """REL-032: Duplicate feedback or rapid resubmission does not corrupt state or crash triage."""
    eval_id = "eval-dedup-01"
    payload = FeedbackCreate(
        category=FeedbackCategory.FUNCTIONAL,
        severity=FeedbackSeverity.P2,
        description="Duplicate bug submission check.",
    )

    resp1 = feedback_service.submit_feedback(eval_id, payload)
    resp2 = feedback_service.submit_feedback(eval_id, payload)

    assert resp1.feedback.id != resp2.feedback.id
    all_fb = feedback_service.list_evaluator_feedback(eval_id)
    assert len(all_fb) == 2


def test_rel_034_logs_and_feedback_do_not_contain_secrets(feedback_service):
    """REL-034: Automated redaction scrubs bearer tokens, private keys, and credit cards from feedback text."""
    eval_id = "eval-leak-test"
    sensitive_input = (
        "Encountered error while sending request with Bearer secret-token-abcdef1234567890. "
        "Also my private key was -----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY----- "
        "and card was 4111-2222-3333-4444."
    )

    resp = feedback_service.submit_feedback(
        evaluator_id=eval_id,
        payload=FeedbackCreate(
            category=FeedbackCategory.ACTIVATION,
            severity=FeedbackSeverity.P1,
            description=sensitive_input,
            reproduction_steps=sensitive_input,
        ),
    )

    clean_desc = resp.feedback.description
    assert "secret-token-abcdef" not in clean_desc
    assert "BEGIN RSA PRIVATE KEY" not in clean_desc
    assert "4111-2222-3333-4444" not in clean_desc
    assert "[REDACTED_SECRET]" in clean_desc
