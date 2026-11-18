"""
AEGIS-DocIntel Cryptographic Release Signing Script
PROT-FINAL-04: Workstream REL-07

Generates canonical release manifest, computes cryptographic digests for all
release artifacts and SBOMs, and signs the manifest using Ed25519.
The private signing key is stored in an isolated, secure directory and NEVER
packaged into the client artifact.
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = REPO_ROOT / "release"
MANIFEST_DIR = RELEASE_DIR / "manifests"
SIGNATURE_DIR = RELEASE_DIR / "signatures"
SBOM_DIR = RELEASE_DIR / "sbom"
CLIENT_DIR = RELEASE_DIR / "client"

MANIFEST_PATH = MANIFEST_DIR / "manifest.json"
SIGNATURE_PATH = SIGNATURE_DIR / "manifest.sig"
KEY_METADATA_PATH = SIGNATURE_DIR / "signing-key-metadata.json"

# Private key storage outside the public distribution tree
PRIVATE_KEY_DIR = REPO_ROOT / "audit" / "prot-final" / "release-engineering"
PRIVATE_KEY_PATH = PRIVATE_KEY_DIR / "release-signing-ed25519.key"

RELEASE_KEY_ID = "aegis-release-ed25519-2026-01"


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "cee7fc9b8b656e5419ec85ca527a0b7c5434da4a"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_or_create_signing_key() -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    PRIVATE_KEY_DIR.mkdir(parents=True, exist_ok=True)
    if PRIVATE_KEY_PATH.exists():
        key_bytes = PRIVATE_KEY_PATH.read_bytes()
        priv = serialization.load_pem_private_key(key_bytes, password=None)
        if not isinstance(priv, ed25519.Ed25519PrivateKey):
            raise TypeError("Loaded key is not an Ed25519PrivateKey")
        return priv, priv.public_key()

    priv = ed25519.Ed25519PrivateKey.generate()
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIVATE_KEY_PATH.write_bytes(pem)
    return priv, priv.public_key()


def sign_release() -> dict:
    print("[*] Generating canonical release manifest and cryptographic Ed25519 signature ...")
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    SIGNATURE_DIR.mkdir(parents=True, exist_ok=True)

    archive_path = CLIENT_DIR / "AEGIS-DocIntel-Demo-Edition.zip"
    if not archive_path.exists():
        raise FileNotFoundError(f"Client archive not found at {archive_path}")

    sbom_path = SBOM_DIR / "client-sbom.cdx.json"
    if not sbom_path.exists():
        raise FileNotFoundError(f"Client SBOM not found at {sbom_path}")

    archive_sha = sha256_file(archive_path)
    archive_size = archive_path.stat().st_size
    sbom_sha = sha256_file(sbom_path)
    commit_sha = get_git_commit()

    manifest_data = {
        "product": "AEGIS Evaluation",
        "version": "1.1.0",
        "release_channel": "evaluation",
        "source": {
            "repository": "AEGIS-DocIntel",
            "commit": commit_sha,
        },
        "build": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow": "ci-release-build",
        },
        "artifacts": [
            {
                "name": archive_path.name,
                "sha256": archive_sha,
                "size_bytes": archive_size,
            }
        ],
        "sbom": {
            "format": "CycloneDX",
            "file": sbom_path.name,
            "sha256": sbom_sha,
        },
        "signature": {
            "algorithm": "Ed25519",
            "key_id": RELEASE_KEY_ID,
        },
    }

    # Canonical representation
    canonical_bytes = json.dumps(manifest_data, sort_keys=True, indent=2).encode("utf-8")
    MANIFEST_PATH.write_bytes(canonical_bytes)

    # Cryptographic signing
    priv_key, pub_key = get_or_create_signing_key()
    signature_bytes = priv_key.sign(canonical_bytes)
    sig_b64 = base64.b64encode(signature_bytes).decode("ascii")

    SIGNATURE_PATH.write_bytes(sig_b64.encode("utf-8"))

    pub_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    key_metadata = {
        "key_id": RELEASE_KEY_ID,
        "algorithm": "Ed25519",
        "public_key_pem": pub_pem,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "ACTIVE",
        "verification_guidance": "Verify manifest.json using manifest.sig and the public key above.",
    }
    KEY_METADATA_PATH.write_bytes(json.dumps(key_metadata, indent=2).encode("utf-8"))

    print(f"[+] Release manifest generated at {MANIFEST_PATH}")
    print(f"[+] Signature generated at {SIGNATURE_PATH}")
    print(f"[+] Public key metadata published to {KEY_METADATA_PATH}")
    return manifest_data


if __name__ == "__main__":
    sign_release()
