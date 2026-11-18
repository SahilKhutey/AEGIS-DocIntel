"""
AEGIS-DocIntel Release Tests: Module 2
PROT-FINAL-08: Evaluator Onboarding, Activation, and Device Binding
Covers: REL-008, REL-009, REL-010, REL-011, REL-021, REL-026
"""

from __future__ import annotations

import base64
from pathlib import Path
import pytest
from fastapi import HTTPException
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.schemas.evaluation.evaluator import EvaluatorCreate, EvaluatorStatus
from src.services.evaluation.evaluator_service import EvaluatorService
from src.services.evaluation.invitation_service import InvitationService
from src.services.evaluation.onboarding_service import OnboardingService
from services.evaluation_gateway.activation import ActivationService

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@pytest.fixture
def onboarding_fixture():
    eval_repo = EvaluatorRepository()
    eval_service = EvaluatorService(repo=eval_repo)
    inv_service = InvitationService(evaluator_repo=eval_repo)
    gateway_act_service = ActivationService()

    onb_service = OnboardingService(
        evaluator_service_inst=eval_service,
        invitation_service_inst=inv_service,
    )

    evaluator = eval_service.create_evaluator(
        EvaluatorCreate(
            organization="Beta Corp",
            display_name="Beta Evaluator",
            contact_email="beta.eval@example.com",
            evaluation_purpose="Evaluation of Document Intelligence",
            initial_status=EvaluatorStatus.INVITED,
        )
    )

    return {
        "eval_repo": eval_repo,
        "eval_service": eval_service,
        "inv_service": inv_service,
        "onb_service": onb_service,
        "gateway_act_service": gateway_act_service,
        "evaluator": evaluator,
    }


def test_rel_008_launch_without_activation(onboarding_fixture):
    """REL-008: Unactivated client status blocks workspace operations and requires activation."""
    onb = onboarding_fixture["onb_service"]
    evaluator = onboarding_fixture["evaluator"]

    assert evaluator.status == EvaluatorStatus.INVITED
    with pytest.raises(ValueError) as exc:
        onb.issue_evaluation_license(evaluator_id=evaluator.evaluator_id)
    assert "Must be REGISTERED" in str(exc.value)


def test_rel_009_valid_evaluator_activation_flow(onboarding_fixture):
    """REL-009: End-to-end activation: invite -> accept -> issue license -> register device -> ACTIVE."""
    onb = onboarding_fixture["onb_service"]
    gateway_act = onboarding_fixture["gateway_act_service"]
    evaluator = onboarding_fixture["evaluator"]

    # 1. Issue invite
    inv_resp = onb.start_onboarding(evaluator_id=evaluator.evaluator_id, operator_id="admin")
    assert inv_resp.raw_token is not None

    # 2. Complete registration
    reg_profile = onb.complete_registration(
        token=inv_resp.raw_token,
        accept_agreement=True,
        acknowledge_privacy=True,
    )
    assert reg_profile.status == EvaluatorStatus.REGISTERED

    # 3. Issue evaluation license
    lic_data = onb.issue_evaluation_license(
        evaluator_id=evaluator.evaluator_id,
        duration_days=14,
        device_limit=1,
    )
    license_id = lic_data.get("license_id") or lic_data["payload"]["license_id"]
    assert license_id is not None

    # 4. Generate device Ed25519 keypair and register activation code
    device_priv_key = ed25519.Ed25519PrivateKey.generate()
    device_pub_pem = device_priv_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    act_code = "ACT-TEST-001"
    gateway_act.register_activation_code(
        code=act_code,
        tier="evaluation",
        max_devices=1,
        user_id=evaluator.evaluator_id,
    )

    # Challenge - Response device registration
    challenge_dict = gateway_act.create_device_challenge(
        activation_code=act_code,
        device_public_key=device_pub_pem,
        installation_id="inst-98765",
        platform="windows",
        client_ip="127.0.0.1",
    )
    ch_id = challenge_dict["challenge_id"]
    canonical_msg = challenge_dict["canonical_message"]

    sig = device_priv_key.sign(canonical_msg.encode("utf-8"))
    sig_b64 = base64.b64encode(sig).decode("ascii")

    act_result = gateway_act.activate_device_with_challenge(
        challenge_id=ch_id,
        signature=sig_b64,
        installation_id="inst-98765",
    )
    assert act_result["device_id"] is not None
    assert act_result["session"]["access_token"] is not None

    # 5. Confirm device activated in onboarding service
    active_profile = onb.confirm_device_activated(
        evaluator_id=evaluator.evaluator_id,
        device_id=act_result["device_id"],
    )
    assert active_profile.status == EvaluatorStatus.ACTIVE


def test_rel_010_invalid_activation_code_rejected(onboarding_fixture):
    """REL-010: Invalid activation code is immediately rejected."""
    gateway_act = onboarding_fixture["gateway_act_service"]

    dev_key = ed25519.Ed25519PrivateKey.generate()
    dev_pem = dev_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    with pytest.raises(ValueError) as exc:
        gateway_act.create_device_challenge(
            activation_code="INVALID-CODE-9999",
            device_public_key=dev_pem,
            installation_id="inst-000",
        )
    assert "invalid" in str(exc.value).lower() or "unrecognized" in str(exc.value).lower()


def test_rel_011_second_device_exceeds_policy_denied(onboarding_fixture):
    """REL-011: Attempting to bind a second device when limit is 1 is denied."""
    gateway_act = onboarding_fixture["gateway_act_service"]
    evaluator = onboarding_fixture["evaluator"]

    act_code = "ACT-DEV-LIMIT-1"
    gateway_act.register_activation_code(
        code=act_code,
        tier="evaluation",
        max_devices=1,
        user_id=evaluator.evaluator_id,
    )

    # Register Device 1
    dev1_key = ed25519.Ed25519PrivateKey.generate()
    dev1_pem = dev1_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    c1 = gateway_act.create_device_challenge(
        activation_code=act_code,
        device_public_key=dev1_pem,
        installation_id="inst-1",
    )
    sig1 = base64.b64encode(dev1_key.sign(c1["canonical_message"].encode("utf-8"))).decode("ascii")
    gateway_act.activate_device_with_challenge(
        challenge_id=c1["challenge_id"],
        signature=sig1,
        installation_id="inst-1",
    )

    # Attempt Register Device 2 (different key)
    dev2_key = ed25519.Ed25519PrivateKey.generate()
    dev2_pem = dev2_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    with pytest.raises(PermissionError) as exc:
        gateway_act.create_device_challenge(
            activation_code=act_code,
            device_public_key=dev2_pem,
            installation_id="inst-2",
        )
    assert "Device limit exceeded" in str(exc.value)


def test_rel_021_development_authentication_bypass_absent():
    """REL-021: Production evaluation environment strictly disallows dev tokens or unsupported roles."""
    from src.api.auth import validate_token_roles
    fake_dev_token = {"sub": "evaluator-1", "tenant_id": "eval-1", "role": "dev-admin"}
    with pytest.raises(HTTPException) as exc:
        validate_token_roles(fake_dev_token)
    assert exc.value.status_code == 401
    assert "Unsupported role" in exc.value.detail


def test_rel_026_revoked_device_cannot_create_new_sessions(onboarding_fixture):
    """REL-026: Deactivating or revoking a device marks it inactive and blocks refresh."""
    gateway_act = onboarding_fixture["gateway_act_service"]
    evaluator = onboarding_fixture["evaluator"]

    act_code = "ACT-DEACT-TEST"
    gateway_act.register_activation_code(
        code=act_code,
        tier="evaluation",
        max_devices=1,
        user_id=evaluator.evaluator_id,
    )

    dev_key = ed25519.Ed25519PrivateKey.generate()
    dev_pem = dev_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    c = gateway_act.create_device_challenge(
        activation_code=act_code,
        device_public_key=dev_pem,
        installation_id="inst-deact",
    )
    sig = base64.b64encode(dev_key.sign(c["canonical_message"].encode("utf-8"))).decode("ascii")
    res = gateway_act.activate_device_with_challenge(
        challenge_id=c["challenge_id"],
        signature=sig,
        installation_id="inst-deact",
    )
    device_id = res["device_id"]
    license_id = res["license"]["license_id"]
    refresh_token = res["session"]["refresh_token"]

    # Deactivate device
    deact_res = gateway_act.deactivate_device(license_id=license_id, device_id_or_pubkey=device_id)
    assert deact_res is True

    # Refreshing session on a deactivated device is strictly denied
    with pytest.raises(PermissionError) as exc:
        gateway_act.refresh_session(refresh_token)
    assert "revoked" in str(exc.value).lower() or "deactivated" in str(exc.value).lower()
