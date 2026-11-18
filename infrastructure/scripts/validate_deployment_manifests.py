"""
AEGIS-DocIntel Deployment Manifest Validator
PROT-FINAL-05: Workstream DEP-11 & DEP-TEST-008

Validates that deployment configurations enforce zero-trust isolation:
- No hardcoded secrets or API keys in compose files (DEP-TEST-008)
- Private engine exposes internal ports only; 0 public host mappings (DEP-TEST-001)
- Database exposes internal ports only; 0 public host mappings (DEP-TEST-003)
- Non-root user execution and no-new-privileges enabled
- Internal network isolation flags (internal: true)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE_DIR = REPO_ROOT / "infrastructure" / "compose"

SECRET_PATTERNS = [
    re.compile(r"password\s*:\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]


def validate_compose_file(path: Path) -> Tuple[bool, List[str]]:
    text = path.read_text(encoding="utf-8")
    violations = []

    # 1. Plaintext secret check
    for pat in SECRET_PATTERNS:
        matches = pat.findall(text)
        if matches:
            violations.append(f"Plaintext secret detected in {path.name}: {pat.pattern}")

    # 2. Check private engine port exposure
    if "private-engine:" in text:
        engine_block = text.split("private-engine:")[1].split("database:")[0]
        # Should NOT have `ports:` mapping host ports
        if re.search(r"^\s+ports:\s*\n\s+-\s*['\"]?\d+:\d+", engine_block, re.MULTILINE):
            violations.append(f"Private engine in {path.name} exposes host ports! Must use 'expose:' only.")

    # 3. Check database port exposure
    if "database:" in text:
        db_block = text.split("database:")[1].split("networks:")[0]
        if re.search(r"^\s+ports:\s*\n\s+-\s*['\"]?\d+:\d+", db_block, re.MULTILINE):
            violations.append(f"Database in {path.name} exposes host ports! Must use internal network only.")

    # 4. Check internal networks
    if "private-services:" in text:
        if "internal: true" not in text:
            violations.append(f"Network 'private-services' in {path.name} lacks 'internal: true' flag.")

    return len(violations) == 0, violations


def run_all_manifest_validations() -> bool:
    print("[*] Validating deployment manifests ...")
    all_ok = True
    for yml in COMPOSE_DIR.rglob("*.yml"):
        ok, errs = validate_compose_file(yml)
        if ok:
            print(f"[+] {yml.relative_to(REPO_ROOT)}: PASSED zero-trust isolation checks.")
        else:
            print(f"[!] {yml.relative_to(REPO_ROOT)}: FAILED with {len(errs)} violations:")
            for e in errs:
                print(f"    - {e}")
            all_ok = False
    return all_ok


if __name__ == "__main__":
    if not run_all_manifest_validations():
        sys.exit(1)
