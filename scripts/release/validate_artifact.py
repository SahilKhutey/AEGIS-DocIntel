"""
AEGIS-DocIntel Artifact Boundary Validation Script
PROT-FINAL-04: Workstream REL-01 / REL-06

Validates that the assembled release artifact adheres strictly to the
distribution boundary, containing zero secrets, private engine code, internal
hostnames, or unapproved files.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = REPO_ROOT / "release"
ARCHIVE_PATH = RELEASE_DIR / "client" / "AEGIS-DocIntel-Demo-Edition.zip"
REPORT_PATH = RELEASE_DIR / "reports" / "artifact-boundary-report.json"

PROHIBITED_EXTENSIONS = {".py", ".pyc", ".pyo", ".pyd", ".map", ".key"}
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
    re.compile(r"postgresql://[^:]+:[^@]+@", re.IGNORECASE),
    re.compile(r"mongodb(\+srv)?://[^:]+:[^@]+@", re.IGNORECASE),
]
INTERNAL_DOMAIN_PATTERNS = [
    re.compile(r"[a-zA-Z0-9_\-\.]+\.(internal|corp|local|lan)"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_artifact() -> dict:
    print(f"[*] Validating release artifact boundary on {ARCHIVE_PATH} ...")
    if not ARCHIVE_PATH.exists():
        raise FileNotFoundError(f"Release archive not found at {ARCHIVE_PATH}. Run assemble_client.py first.")

    violations = []
    scanned_files = []

    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zf:
        namelist = zf.namelist()
        for name in namelist:
            if name.endswith("/"):
                continue  # Directory entry

            scanned_files.append(name)
            p = Path(name)
            
            # Extension check
            if p.suffix.lower() in PROHIBITED_EXTENSIONS:
                violations.append({"file": name, "reason": f"Prohibited file extension '{p.suffix}'"})

            # Name check
            if p.name.startswith(".env"):
                violations.append({"file": name, "reason": "Prohibited .env configuration file"})

            # Read content
            raw_data = zf.read(name)
            try:
                text = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                text = ""

            if text:
                for pat in SECRET_PATTERNS:
                    if pat.search(text):
                        violations.append({"file": name, "reason": f"Credential/Secret pattern match: {pat.pattern}"})
                for pat in INTERNAL_DOMAIN_PATTERNS:
                    if pat.search(text):
                        violations.append({"file": name, "reason": f"Internal domain pattern match: {pat.pattern}"})

    is_compliant = len(violations) == 0
    report = {
        "status": "COMPLIANT" if is_compliant else "VIOLATIONS_DETECTED",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "archive_path": str(ARCHIVE_PATH.relative_to(REPO_ROOT)),
        "archive_sha256": hashlib.sha256(ARCHIVE_PATH.read_bytes()).hexdigest(),
        "total_files_scanned": len(scanned_files),
        "violations_count": len(violations),
        "violations": violations,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if not is_compliant:
        print(f"[!] Validation FAILED with {len(violations)} violations.")
        for v in violations:
            print(f"    - {v['file']}: {v['reason']}")
        sys.exit(1)

    print(f"[+] Artifact boundary validation PASSED: {len(scanned_files)} files cleanly verified.")
    return report


if __name__ == "__main__":
    validate_artifact()
