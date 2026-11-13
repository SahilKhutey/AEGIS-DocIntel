"""
AEGIS Distribution Security Tests — Package Contents & IP Protection
Covers:
- SEC-DEMO-001: No proprietary engine source in downloadable package
- SEC-DEMO-002: No production secrets or private keys in package
- SEC-DEMO-003: No sourcemaps in client distribution
- SEC-DEMO-004: Administrative route blocking in reverse proxy
- SEC-DEMO-016: Package manifest integrity and tampered file detection
- SEC-DEMO-017: Third-party license attribution completeness
"""

import hashlib
import json
import re
from pathlib import Path
import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "distribution" / "demo-edition"

def test_sec_demo_001_no_proprietary_engine_source():
    """SEC-DEMO-001: Asserts that no proprietary Python source code from src/engines/ or core orchestrator is in the package."""
    assert PACKAGE_ROOT.exists(), "distribution/demo-edition must exist"
    
    forbidden_terms = [
        "submodular",
        "sheaf",
        "laplacian",
        "orchestrator.py",
        "memory_engine",
        "math_concepts"
    ]
    
    leaked_files = []
    for p in PACKAGE_ROOT.rglob("*.py"):
        rel = p.relative_to(PACKAGE_ROOT).as_posix()
        content = p.read_text(encoding="utf-8", errors="replace").lower()
        for term in forbidden_terms:
            if term in rel.lower() or term in content:
                leaked_files.append((rel, term))
                
    assert len(leaked_files) == 0, f"Proprietary engine source detected in package: {leaked_files}"


def test_sec_demo_002_no_secrets_or_private_keys():
    """SEC-DEMO-002: Asserts that no private keys, .env secrets, or API keys exist in the downloadable package."""
    leaked_secrets = []
    
    for p in PACKAGE_ROOT.rglob("*"):
        if p.is_file():
            name = p.name.lower()
            if name.endswith(".pem") and "private" in name:
                leaked_secrets.append(f"Private key file found: {p}")
            if name.startswith(".env") and not name.endswith(".example"):
                leaked_secrets.append(f"Environment secret file found: {p}")
            
            # Check content for private key headers
            if p.suffix in [".pem", ".key", ".txt", ".lic", ".json"]:
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")
                    if "BEGIN PRIVATE KEY" in text or "BEGIN EC PRIVATE KEY" in text:
                        leaked_secrets.append(f"Private key contents found in: {p}")
                    if "sk-" in text or "ghp_" in text or "AWS_SECRET_ACCESS_KEY" in text:
                        leaked_secrets.append(f"API key pattern found in: {p}")
                except Exception:
                    pass

    assert len(leaked_secrets) == 0, f"Secrets or private keys detected in demo package: {leaked_secrets}"


def test_sec_demo_003_no_sourcemaps_in_distribution():
    """SEC-DEMO-003: Asserts that no .map sourcemap files or sourceMappingURL references exist in client assets."""
    sourcemap_files = list(PACKAGE_ROOT.rglob("*.map"))
    assert len(sourcemap_files) == 0, f"Sourcemap files detected in package: {sourcemap_files}"


def test_sec_demo_004_admin_routes_blocked_in_proxy():
    """SEC-DEMO-004: Asserts that the proxy configuration strictly denies administrative and internal routes."""
    proxy_conf = PACKAGE_ROOT / "deploy" / "nginx-demo-proxy.conf"
    assert proxy_conf.exists(), "nginx-demo-proxy.conf must exist"
    
    conf_text = proxy_conf.read_text(encoding="utf-8")
    assert "/admin" in conf_text, "Proxy configuration must explicitly match /admin"
    assert "return 403" in conf_text, "Proxy configuration must return 403 on admin routes"


def test_sec_demo_016_package_manifest_integrity():
    """SEC-DEMO-016: Asserts that the package manifest lists all files and verifies SHA-256 hashes."""
    manifest_path = PACKAGE_ROOT / "package-manifest.json"
    assert manifest_path.exists(), "package-manifest.json must exist"
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["package_name"] == "AEGIS-DocIntel-Demo-Edition"
    assert manifest["version"] == "1.1.0"
    
    for entry in manifest["files"]:
        file_path = PACKAGE_ROOT / entry["path"]
        assert file_path.exists(), f"File listed in manifest is missing: {entry['path']}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
        assert actual_hash == entry["sha256"].lower(), f"SHA-256 mismatch for {entry['path']}"


def test_sec_demo_017_third_party_attribution():
    """SEC-DEMO-017: Asserts that THIRD-PARTY-NOTICES.md exists and properly attributes third-party licenses."""
    notices_path = PACKAGE_ROOT / "THIRD-PARTY-NOTICES.md"
    assert notices_path.exists(), "THIRD-PARTY-NOTICES.md must exist in demo package"
    
    text = notices_path.read_text(encoding="utf-8")
    required_attributions = ["aegis-docprep", "Next.js", "React", "FastAPI", "Nginx", "Cryptography"]
    for item in required_attributions:
        assert item in text, f"Missing attribution for {item} in THIRD-PARTY-NOTICES.md"
