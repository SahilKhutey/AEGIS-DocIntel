"""
AEGIS-DocIntel Independent Release Verification Script
PROT-FINAL-04: Workstream REL-07 / REL-08

Verifies the cryptographic Ed25519 signature on manifest.json, checks the
integrity of the release archive against the signed digest, and confirms
SBOM hash continuity. Suitable for independent evaluation verification.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = REPO_ROOT / "release"
MANIFEST_PATH = RELEASE_DIR / "manifests" / "manifest.json"
SIGNATURE_PATH = RELEASE_DIR / "signatures" / "manifest.sig"
KEY_METADATA_PATH = RELEASE_DIR / "signatures" / "signing-key-metadata.json"
CLIENT_DIR = RELEASE_DIR / "client"
SBOM_DIR = RELEASE_DIR / "sbom"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_release() -> bool:
    print("[*] Performing independent release verification ...")

    # 1. Check file existence
    for req_file in (MANIFEST_PATH, SIGNATURE_PATH, KEY_METADATA_PATH):
        if not req_file.exists():
            raise FileNotFoundError(f"Verification prerequisite missing: {req_file}")

    # 2. Load public key
    meta = json.loads(KEY_METADATA_PATH.read_text(encoding="utf-8"))
    pub_pem = meta["public_key_pem"].encode("utf-8")
    pub_key = serialization.load_pem_public_key(pub_pem)
    if not isinstance(pub_key, ed25519.Ed25519PublicKey):
        raise TypeError("Published public key is not an Ed25519PublicKey")

    # 3. Load signature and manifest
    sig_b64 = SIGNATURE_PATH.read_text(encoding="utf-8").strip()
    signature_bytes = base64.b64decode(sig_b64)
    manifest_bytes = MANIFEST_PATH.read_bytes()

    try:
        pub_key.verify(signature_bytes, manifest_bytes)
        print("[+] Manifest cryptographic signature VALID (Ed25519).")
    except InvalidSignature:
        print("[!] FATAL: Manifest cryptographic signature INVALID! Tampering detected.")
        sys.exit(1)

    # 4. Parse manifest and verify artifact digests
    manifest = json.loads(manifest_bytes.decode("utf-8"))

    # Verify artifacts
    for art in manifest.get("artifacts", []):
        art_name = art["name"]
        expected_sha = art["sha256"]
        art_path = CLIENT_DIR / art_name
        if not art_path.exists():
            raise FileNotFoundError(f"Declared artifact missing: {art_path}")

        actual_sha = sha256_file(art_path)
        if actual_sha != expected_sha:
            print(f"[!] FATAL: SHA-256 mismatch for {art_name}!")
            print(f"    Expected: {expected_sha}")
            print(f"    Actual:   {actual_sha}")
            sys.exit(1)
        print(f"[+] Artifact digest matches signed manifest: {art_name} ({actual_sha})")

    # Verify SBOM
    sbom_info = manifest.get("sbom", {})
    sbom_name = sbom_info.get("file")
    expected_sbom_sha = sbom_info.get("sha256")
    sbom_path = SBOM_DIR / sbom_name
    if not sbom_path.exists():
        raise FileNotFoundError(f"Declared SBOM missing: {sbom_path}")

    actual_sbom_sha = sha256_file(sbom_path)
    if actual_sbom_sha != expected_sbom_sha:
        print("[!] FATAL: SBOM SHA-256 mismatch!")
        print(f"    Expected: {expected_sbom_sha}")
        print(f"    Actual:   {actual_sbom_sha}")
        sys.exit(1)
    print(f"[+] SBOM digest matches signed manifest: {sbom_name} ({actual_sbom_sha})")

    print("[SUCCESS] All release verification checks passed! Artifact is authentic and untampered.")
    return True


if __name__ == "__main__":
    verify_release()
