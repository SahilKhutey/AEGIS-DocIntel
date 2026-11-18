"""
AEGIS-DocIntel Secure Client Assembly Script
PROT-FINAL-04: Workstream REL-01

Enforces strict client distribution boundaries by allowlisting only approved
public client artifacts, excluding private backend, engine, and test files,
and producing a deterministic distribution archive.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEMO_SRC = REPO_ROOT / "distribution" / "demo-edition"
RELEASE_DIR = REPO_ROOT / "release"
CLIENT_DIR = RELEASE_DIR / "client"
CLIENT_STAGING = CLIENT_DIR / "AEGIS-DocIntel-Demo-Edition"
ARCHIVE_PATH = CLIENT_DIR / "AEGIS-DocIntel-Demo-Edition.zip"

ALLOWLIST_PATTERNS = [
    "README.md",
    "LICENSE-EVALUATION.md",
    "THIRD-PARTY-NOTICES.md",
    "package-manifest.json",
    "deploy/compose.yaml",
    "deploy/nginx-demo-proxy.conf",
    "launcher/start-demo.ps1",
    "launcher/start-demo.sh",
    "launcher/stop-demo.ps1",
    "launcher/stop-demo.sh",
    "launcher/status-demo.ps1",
    "launcher/reset-demo.ps1",
    "launcher/verify-package.ps1",
    "license/evaluation.lic",
    "license/public-key.pem",
    "demo-data/**",
    "THIRD-PARTY-NOTICES/**",
]

PROHIBITED_EXTENSIONS = {
    ".py", ".pyc", ".pyo", ".pyd",
    ".map", ".ts", ".tsx",
    ".env", ".key",
}

PROHIBITED_SUBSTRINGS = [
    "BEGIN PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN EC PRIVATE KEY",
    "sk-",
    "ghp_",
    "AKIA",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def is_allowlisted(rel_path: str) -> bool:
    posix_path = rel_path.replace("\\", "/")
    for pattern in ALLOWLIST_PATTERNS:
        if pattern.endswith("/**"):
            prefix = pattern[:-3]
            if posix_path.startswith(prefix):
                return True
        elif posix_path == pattern:
            return True
    return False


def assemble_client() -> dict:
    print(f"[*] Assembling client from {DEMO_SRC} into {CLIENT_STAGING} ...")
    if CLIENT_STAGING.exists():
        shutil.rmtree(CLIENT_STAGING)
    CLIENT_STAGING.mkdir(parents=True, exist_ok=True)

    included_files = []
    rejected_files = []

    for root, _, files in os.walk(DEMO_SRC):
        for fname in files:
            full_path = Path(root) / fname
            rel_path = full_path.relative_to(DEMO_SRC).as_posix()

            # Boundary validation
            suffix = full_path.suffix.lower()
            if suffix in PROHIBITED_EXTENSIONS or fname.startswith(".env"):
                rejected_files.append((rel_path, f"Prohibited extension or name: {suffix}"))
                continue

            if not is_allowlisted(rel_path):
                rejected_files.append((rel_path, "Not in client distribution allowlist"))
                continue

            # Read text and check for secret markers
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                violates = False
                for marker in PROHIBITED_SUBSTRINGS:
                    if marker in content:
                        rejected_files.append((rel_path, f"Prohibited secret marker: {marker}"))
                        violates = True
                        break
                if violates:
                    continue
            except Exception:
                pass

            target_path = CLIENT_STAGING / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full_path, target_path)

            file_hash = sha256_file(target_path)
            file_size = target_path.stat().st_size
            included_files.append({
                "path": rel_path,
                "sha256": file_hash,
                "size_bytes": file_size,
            })

    if rejected_files:
        print(f"[!] Warning: {len(rejected_files)} files rejected during assembly: {rejected_files}")

    # Build deterministic zip archive
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    print(f"[*] Packaging deterministic archive {ARCHIVE_PATH} ...")
    with zipfile.ZipFile(ARCHIVE_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(CLIENT_STAGING):
            for fname in sorted(files):
                fpath = Path(root) / fname
                arcname = f"AEGIS-DocIntel-Demo-Edition/{fpath.relative_to(CLIENT_STAGING).as_posix()}"
                
                # Normalize zip metadata for reproducibility (epoch timestamp 2026-01-01 00:00:00)
                zinfo = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
                zinfo.compress_type = zipfile.ZIP_DEFLATED
                zinfo.external_attr = 0o644 << 16  # standard non-executable permissions
                
                with open(fpath, "rb") as fp:
                    zf.writestr(zinfo, fp.read())

    archive_sha = sha256_file(ARCHIVE_PATH)
    archive_size = ARCHIVE_PATH.stat().st_size

    assembly_summary = {
        "status": "SUCCESS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_files": len(included_files),
        "archive": {
            "name": ARCHIVE_PATH.name,
            "sha256": archive_sha,
            "size_bytes": archive_size,
        },
        "files": included_files,
        "rejected_count": len(rejected_files),
    }

    report_path = RELEASE_DIR / "reports" / "build-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(assembly_summary, indent=2), encoding="utf-8")
    print(f"[+] Assembly complete. Included {len(included_files)} files. Archive SHA-256: {archive_sha}")
    return assembly_summary


if __name__ == "__main__":
    assemble_client()
