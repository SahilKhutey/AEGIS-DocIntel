"""
Release Engineering Test Suite — Artifact Cryptographic Signing (REL-008, GATE-08, GATE-09)
PROT-FINAL-04: Workstream REL-07
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import pytest

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "release" / "manifests" / "manifest.json"
SIGNATURE_PATH = REPO_ROOT / "release" / "signatures" / "manifest.sig"
KEY_METADATA_PATH = REPO_ROOT / "release" / "signatures" / "signing-key-metadata.json"
CLIENT_ARCHIVE = REPO_ROOT / "release" / "client" / "AEGIS-DocIntel-Demo-Edition.zip"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_rel_041_manifest_and_signature_exist():
    """REL-008.1: Confirms presence of manifest, signature, and public key metadata."""
    assert MANIFEST_PATH.exists()
    assert SIGNATURE_PATH.exists()
    assert KEY_METADATA_PATH.exists()


def test_rel_042_ed25519_signature_verifies():
    """REL-008.2: Verifies that manifest.sig validates against manifest.json using published public key."""
    meta = json.loads(KEY_METADATA_PATH.read_text(encoding="utf-8"))
    pub_key = serialization.load_pem_public_key(meta["public_key_pem"].encode("utf-8"))
    assert isinstance(pub_key, ed25519.Ed25519PublicKey)

    sig_bytes = base64.b64decode(SIGNATURE_PATH.read_text(encoding="utf-8").strip())
    manifest_bytes = MANIFEST_PATH.read_bytes()

    # Must verify cleanly
    pub_key.verify(sig_bytes, manifest_bytes)


def test_rel_043_tampered_manifest_fails_verification():
    """GATE-09: Verifies that any tampering with manifest.json fails cryptographic verification."""
    meta = json.loads(KEY_METADATA_PATH.read_text(encoding="utf-8"))
    pub_key = serialization.load_pem_public_key(meta["public_key_pem"].encode("utf-8"))

    sig_bytes = base64.b64decode(SIGNATURE_PATH.read_text(encoding="utf-8").strip())
    manifest_bytes = MANIFEST_PATH.read_bytes()

    # Tamper one byte
    tampered_bytes = manifest_bytes.replace(b"AEGIS Evaluation", b"AEGIS Tampered")
    with pytest.raises(InvalidSignature):
        pub_key.verify(sig_bytes, tampered_bytes)


def test_rel_044_archive_digest_matches_manifest():
    """GATE-08: Verifies that the release archive SHA-256 strictly matches the signed manifest."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    declared_artifacts = manifest.get("artifacts", [])
    assert len(declared_artifacts) > 0
    
    first_art = declared_artifacts[0]
    expected_sha = first_art["sha256"]
    actual_sha = sha256_file(CLIENT_ARCHIVE)
    assert actual_sha == expected_sha
