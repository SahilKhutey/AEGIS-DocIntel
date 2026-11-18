"""
AEGIS-DocIntel CycloneDX SBOM Generator
PROT-FINAL-04: Workstream REL-05

Generates machine-readable CycloneDX 1.5 JSON Software Bill of Materials (SBOM)
for both the downloadable client package and the private backend deployment.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RELEASE_DIR = REPO_ROOT / "release"
SBOM_DIR = RELEASE_DIR / "sbom"
CLIENT_SBOM_TARGET = SBOM_DIR / "client-sbom.cdx.json"
BACKEND_SBOM_TARGET = SBOM_DIR / "backend-sbom.cdx.json"

SRC_NPM_SBOM = REPO_ROOT / "distribution" / "demo-edition" / "THIRD-PARTY-NOTICES" / "manifest" / "npm-sbom.json"
SRC_PY_SBOM = REPO_ROOT / "distribution" / "demo-edition" / "THIRD-PARTY-NOTICES" / "manifest" / "python-sbom.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_sboms() -> dict:
    print("[*] Generating CycloneDX 1.5 JSON SBOMs ...")
    SBOM_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Client SBOM
    if SRC_NPM_SBOM.exists():
        raw_client = json.loads(SRC_NPM_SBOM.read_text(encoding="utf-8"))
    else:
        raw_client = {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}

    # Enrich client metadata
    raw_client["metadata"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tools": [
            {"vendor": "AEGIS Security Release Engineering", "name": "cyclonedx-enricher", "version": "1.1.0"}
        ],
        "component": {
            "type": "application",
            "name": "aegis-docintel-evaluation-client",
            "version": "1.1.0",
            "description": "AEGIS-DocIntel Downloadable Protected Evaluation Edition",
            "licenses": [{"license": {"id": "Proprietary-Evaluation"}}],
        },
    }

    # Add launcher and container proxy components if not already represented
    launcher_comps = [
        {
            "type": "application",
            "name": "aegis-demo-launcher-powershell",
            "version": "1.1.0",
            "purl": "pkg:generic/aegis-demo-launcher-powershell@1.1.0",
            "licenses": [{"license": {"id": "Proprietary-Evaluation"}}],
        },
        {
            "type": "application",
            "name": "aegis-demo-launcher-posix",
            "version": "1.1.0",
            "purl": "pkg:generic/aegis-demo-launcher-posix@1.1.0",
            "licenses": [{"license": {"id": "Proprietary-Evaluation"}}],
        },
        {
            "type": "container",
            "name": "nginx-alpine",
            "version": "1.27-alpine",
            "purl": "pkg:docker/nginx@1.27-alpine",
            "licenses": [{"license": {"id": "BSD-2-Clause"}}],
        },
    ]

    existing_names = {c.get("name") for c in raw_client.get("components", [])}
    for comp in launcher_comps:
        if comp["name"] not in existing_names:
            raw_client.setdefault("components", []).append(comp)

    CLIENT_SBOM_TARGET.write_text(json.dumps(raw_client, indent=2), encoding="utf-8")
    client_sha = sha256_file(CLIENT_SBOM_TARGET)
    print(f"[+] Client SBOM generated at {CLIENT_SBOM_TARGET} ({len(raw_client.get('components', []))} components, SHA-256: {client_sha})")

    # 2. Backend SBOM
    if SRC_PY_SBOM.exists():
        raw_backend = json.loads(SRC_PY_SBOM.read_text(encoding="utf-8"))
    else:
        raw_backend = {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}

    raw_backend["bomFormat"] = "CycloneDX"
    raw_backend["specVersion"] = "1.5"
    raw_backend["metadata"] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tools": [
            {"vendor": "AEGIS Security Release Engineering", "name": "cyclonedx-py-scanner", "version": "1.1.0"}
        ],
        "component": {
            "type": "application",
            "name": "aegis-docintel-backend-engine",
            "version": "1.1.0",
            "description": "AEGIS-DocIntel Private Core Backend & Evaluation Gateway",
            "licenses": [{"license": {"id": "Proprietary-Confidential"}}],
        },
    }

    BACKEND_SBOM_TARGET.write_text(json.dumps(raw_backend, indent=2), encoding="utf-8")
    backend_sha = sha256_file(BACKEND_SBOM_TARGET)
    print(f"[+] Backend SBOM generated at {BACKEND_SBOM_TARGET} ({len(raw_backend.get('components', []))} components, SHA-256: {backend_sha})")

    return {
        "client_sbom": {
            "path": str(CLIENT_SBOM_TARGET.relative_to(REPO_ROOT)),
            "sha256": client_sha,
            "components_count": len(raw_client.get("components", [])),
        },
        "backend_sbom": {
            "path": str(BACKEND_SBOM_TARGET.relative_to(REPO_ROOT)),
            "sha256": backend_sha,
            "components_count": len(raw_backend.get("components", [])),
        },
    }


if __name__ == "__main__":
    generate_sboms()
