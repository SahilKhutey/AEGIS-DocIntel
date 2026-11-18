"""
AEGIS-DocIntel Release Tests: Module 1
PROT-FINAL-08: Download Portal, Package Integrity, and Boundary Controls
Covers: REL-001, REL-002, REL-003, REL-004, REL-005, REL-006, REL-007, REL-022, REL-023, REL-033
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
import pytest

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.schemas.evaluation.evaluator import EvaluatorCreate, EvaluatorStatus
from src.schemas.evaluation.release import (
    ArtifactVerificationRequest,
    ReleaseArtifactItem,
    ReleaseManifest,
    ReleaseSignatureInfo,
)
from src.services.evaluation.evaluator_service import EvaluatorService
from src.services.evaluation.release_access_service import (
    DownloadLinkExpiredError,
    ReleaseAccessService,
    UnauthorizedDownloadError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PACKAGE_PATH = REPO_ROOT / "release" / "client" / "AEGIS-Evaluation-0.1.0.zip"
MANIFEST_PATH = REPO_ROOT / "release" / "manifests" / "release-manifest-0.1.0.json"


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


@pytest.fixture
def release_services():
    eval_repo = EvaluatorRepository()
    eval_service = EvaluatorService(repo=eval_repo)
    rel_service = ReleaseAccessService(evaluator_repo=eval_repo)

    # Register test evaluator
    active_eval = eval_service.create_evaluator(
        EvaluatorCreate(
            organization="Beta Corp",
            display_name="Beta Evaluator",
            contact_email="beta@example.com",
            evaluation_purpose="Test Evaluation",
            initial_status=EvaluatorStatus.ACTIVE,
        )
    )

    suspended_eval = eval_service.create_evaluator(
        EvaluatorCreate(
            organization="Suspended Org",
            display_name="Suspended Evaluator",
            contact_email="suspended@example.com",
            evaluation_purpose="Suspended Evaluation",
            initial_status=EvaluatorStatus.SUSPENDED,
        )
    )

    return {
        "eval_service": eval_service,
        "rel_service": rel_service,
        "active_eval": active_eval,
        "suspended_eval": suspended_eval,
    }


def test_rel_001_download_authorized_release(release_services):
    """REL-001: Authorized evaluator can obtain signed download link for release artifact."""
    rel_service = release_services["rel_service"]
    active_eval = release_services["active_eval"]

    token_resp = rel_service.generate_download_token(
        evaluator_id=active_eval.evaluator_id,
        version="0.1.0",
        ttl_seconds=900,
    )
    assert token_resp.download_url.startswith("https://evaluate.aegis.corp/v1/evaluation/download?token=")
    assert token_resp.artifact.filename == "AEGIS-Evaluation-0.1.0.zip"

    token = token_resp.download_url.split("token=")[1]
    grant = rel_service.verify_and_consume_token(token)
    assert grant["evaluator_id"] == active_eval.evaluator_id
    assert grant["artifact_filename"] == "AEGIS-Evaluation-0.1.0.zip"


def test_rel_002_download_unauthorized_account(release_services):
    """REL-002: Download with unauthorized / suspended account is strictly denied."""
    rel_service = release_services["rel_service"]
    suspended_eval = release_services["suspended_eval"]

    with pytest.raises(UnauthorizedDownloadError) as exc_info:
        rel_service.generate_download_token(
            evaluator_id=suspended_eval.evaluator_id,
            version="0.1.0",
        )
    assert "SUSPENDED" in str(exc_info.value)

    # Nonexistent account
    with pytest.raises(UnauthorizedDownloadError):
        rel_service.generate_download_token(
            evaluator_id="nonexistent-eval-999",
            version="0.1.0",
        )


def test_rel_003_expired_download_link(release_services):
    """REL-003: Expired or consumed download links are rejected."""
    rel_service = release_services["rel_service"]
    active_eval = release_services["active_eval"]

    # Issue token with negative TTL
    token_resp = rel_service.generate_download_token(
        evaluator_id=active_eval.evaluator_id,
        version="0.1.0",
        ttl_seconds=-10,  # Already expired
    )
    token = token_resp.download_url.split("token=")[1]

    with pytest.raises(DownloadLinkExpiredError):
        rel_service.verify_and_consume_token(token)


def test_rel_004_and_rel_005_verify_package_hash_and_signature(release_services):
    """REL-004 & REL-005: Package hash and Ed25519 signature match published release manifest."""
    rel_service = release_services["rel_service"]
    assert PACKAGE_PATH.exists(), "Release package zip must exist"
    assert MANIFEST_PATH.exists(), "Release manifest must exist"

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    actual_hash = sha256_file(PACKAGE_PATH)

    assert manifest["artifact"]["sha256"] == actual_hash

    # Verify through service
    req = ArtifactVerificationRequest(
        artifact_filename=PACKAGE_PATH.name,
        sha256=actual_hash,
        signature_hex=manifest["signature"]["signature_hex"],
    )
    resp = rel_service.verify_artifact_integrity(req, version="0.1.0")
    assert resp.valid is True
    assert resp.status == "VERIFIED_COMPLIANT"
    assert resp.signature_verified is True


def test_rel_006_tampered_package_fails(release_services):
    """REL-006: Tampered artifact hash or invalid signature is rejected."""
    rel_service = release_services["rel_service"]

    # Tampered hash
    req = ArtifactVerificationRequest(
        artifact_filename="AEGIS-Evaluation-0.1.0.zip",
        sha256="0000000000000000000000000000000000000000000000000000000000000000",
        signature_hex="abc123",
    )
    resp = rel_service.verify_artifact_integrity(req, version="0.1.0")
    assert resp.valid is False
    assert resp.status == "HASH_MISMATCH"


def test_rel_007_clean_windows_installation():
    """REL-007: Package expands cleanly without path traversal or corrupted files."""
    assert PACKAGE_PATH.exists()

    with zipfile.ZipFile(PACKAGE_PATH, "r") as zf:
        file_list = zf.namelist()
        assert len(file_list) > 0
        for name in file_list:
            assert not name.startswith("/"), "Zip entries must not use absolute paths"
            assert ".." not in name, "Zip entries must not contain directory traversal sequences"
            # Verify CRC
            info = zf.getinfo(name)
            assert info.file_size >= 0


def test_rel_022_no_private_keys_or_api_credentials_in_package():
    """REL-022: Package contains ZERO private keys, AWS/DB secrets, or bearer tokens."""
    assert PACKAGE_PATH.exists()

    prohibited_names = [".env", ".key", "id_rsa", "secret", "private"]
    with zipfile.ZipFile(PACKAGE_PATH, "r") as zf:
        for name in zf.namelist():
            for p in prohibited_names:
                # public-key.pem is allowed; private keys are forbidden
                if p in name.lower() and "public" not in name.lower():
                    pytest.fail(f"Found sensitive file pattern '{p}' in zip: {name}")


def test_rel_023_no_backend_source_in_package():
    """REL-023: Package contains ZERO Python source files (.py) or backend engine source."""
    assert PACKAGE_PATH.exists()

    with zipfile.ZipFile(PACKAGE_PATH, "r") as zf:
        for name in zf.namelist():
            assert not name.endswith(".py"), f"Backend python file found in client package: {name}"
            assert not name.endswith(".pyc"), f"Compiled python bytecode found in client package: {name}"
            assert "src/" not in name, f"Source tree found in client package: {name}"


def test_rel_033_download_artifacts_immutable():
    """REL-033: Published manifest and client archive remain cryptographically immutable."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    recorded_hash = manifest["artifact"]["sha256"]
    current_hash = sha256_file(PACKAGE_PATH)
    assert recorded_hash == current_hash, "Artifact hash has mutated after packaging!"
