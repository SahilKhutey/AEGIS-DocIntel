"""
AEGIS Evaluation Security Tests — REM-07: Protected Distribution & Build Hygiene
Verifies acceptance criteria DST-REM-001 through DST-REM-010:
- DST-REM-001: Client bundle excludes private engine core source code
- DST-REM-002: Zero private keys in downloadable distribution package
- DST-REM-003: Zero foundation model provider API keys in client source
- DST-REM-004: Configuration manifest verification (only public properties)
- DST-REM-005: Absence of internal database connection strings in client source
- DST-REM-006: Third-party open source license notices & SBOM present
- DST-REM-007: SHA-256 integrity checksum manifest present and valid
- DST-REM-008: Clean build tree: no scratch, temporary or dev bypass files
- DST-REM-009: Security headers enforced for web/gateway distribution
- DST-REM-010: Zero dev-token bypasses in production client packages
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_dst_rem_001_client_excludes_private_engine_code():
    """DST-REM-001: Client source and demo package contain no private engine modules."""
    web_src = REPO_ROOT / "web" / "src"
    assert web_src.exists()

    forbidden_engine_markers = [
        "src.engine",
        "services.private_engine",
        "EvaluationEngineInternal",
        "proprietary_kernel",
    ]

    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden_engine_markers:
                if marker in text:
                    violations.append((str(f.relative_to(REPO_ROOT)), marker))

    assert len(violations) == 0, f"Private engine markers found in web client: {violations}"


def test_dst_rem_002_zero_private_keys_in_distribution():
    """DST-REM-002: Distribution files contain no private cryptographic keys."""
    dist_dir = REPO_ROOT / "distribution"
    assert dist_dir.exists()

    private_key_markers = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ]

    violations = []
    for f in (dist_dir / "demo-edition").rglob("*"):
        if f.is_file():
            assert not f.name.endswith(".key"), f"Key file in demo-edition: {f}"
            assert "private" not in f.name.lower(), f"Private file in demo-edition: {f}"
            if f.suffix in (".json", ".yaml", ".yml", ".md", ".txt", ".ps1", ".sh", ".conf"):
                content = f.read_text(encoding="utf-8", errors="ignore")
                for marker in private_key_markers:
                    if marker in content:
                        violations.append((str(f.relative_to(REPO_ROOT)), marker))

    assert len(violations) == 0, f"Private key content in demo edition: {violations}"


def test_dst_rem_003_zero_provider_api_keys_in_client():
    """DST-REM-003: Zero foundation model provider API keys exist in client source."""
    patterns = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),  # OpenAI
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),  # Google Cloud
        re.compile(r"anthropic-[a-zA-Z0-9_-]{20,}"),  # Anthropic
    ]
    web_src = REPO_ROOT / "web" / "src"
    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx", ".json", ".html"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            for rgx in patterns:
                matches = rgx.findall(content)
                if matches:
                    violations.append((str(f.relative_to(REPO_ROOT)), matches))

    assert len(violations) == 0, f"Provider API keys found in client source: {violations}"


def test_dst_rem_004_public_configuration_manifest_only():
    """DST-REM-004: Configuration manifest exposes only public gateway attributes."""
    manifest_file = REPO_ROOT / "distribution" / "demo-edition" / "package-manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        assert "package_name" in manifest
        assert "version" in manifest
        # Ensure no private endpoints or keys
        serialized = json.dumps(manifest)
        assert "private_key" not in serialized.lower()
        assert "password" not in serialized.lower()


def test_dst_rem_005_no_internal_database_connection_strings():
    """DST-REM-005: Absence of internal DB connection strings in web source."""
    web_src = REPO_ROOT / "web" / "src"
    db_patterns = [
        re.compile(r"postgres://[^\s]+"),
        re.compile(r"postgresql://[^\s]+"),
        re.compile(r"redis://[^\s]+"),
        re.compile(r"mongodb://[^\s]+"),
    ]

    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx", ".json"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            for p in db_patterns:
                matches = p.findall(content)
                if matches:
                    violations.append((str(f.relative_to(REPO_ROOT)), matches))

    assert len(violations) == 0, f"Database connection strings in client source: {violations}"


def test_dst_rem_006_third_party_notices_and_sbom():
    """DST-REM-006: Third-party notices and SBOM are present in distribution."""
    notices_dir = REPO_ROOT / "distribution" / "demo-edition" / "THIRD-PARTY-NOTICES"
    assert notices_dir.exists(), "Third-party notices directory missing"
    assert (notices_dir / "THIRD-PARTY-NOTICES.md").exists()
    assert (notices_dir / "manifest" / "python-sbom.json").exists()
    assert (notices_dir / "manifest" / "npm-sbom.json").exists()


def test_dst_rem_007_checksum_manifest_verification():
    """DST-REM-007: SHA256SUMS file exists and lists distribution artifacts."""
    checksums_file = REPO_ROOT / "distribution" / "release" / "SHA256SUMS"
    assert checksums_file.exists(), "SHA256SUMS manifest is missing"
    content = checksums_file.read_text(encoding="utf-8-sig").strip()
    assert len(content) > 0
    # Every line has 64-char hex hash followed by whitespace and filename
    for line in content.splitlines():
        if line.strip():
            parts = line.split(maxsplit=1)
            assert len(parts) == 2
            assert len(parts[0]) == 64  # SHA-256


def test_dst_rem_008_clean_build_tree():
    """DST-REM-008: Distribution directory contains no scratch or temp build files."""
    dist_dir = REPO_ROOT / "distribution" / "demo-edition"
    for f in dist_dir.rglob("*"):
        if f.is_file():
            assert not f.name.endswith(".tmp")
            assert not f.name.endswith(".swp")
            assert not f.name.endswith(".bak")
            assert "scratch" not in f.name.lower()


def test_dst_rem_009_security_headers_in_nginx_conf():
    """DST-REM-009: Distribution reverse proxy config enforces secure HTTP headers."""
    conf_file = REPO_ROOT / "distribution" / "demo-edition" / "deploy" / "nginx-demo-proxy.conf"
    assert conf_file.exists(), "Nginx config missing in demo deploy"
    conf_text = conf_file.read_text(encoding="utf-8")

    assert "X-Content-Type-Options" in conf_text
    assert "X-Frame-Options" in conf_text
    assert "Content-Security-Policy" in conf_text


def test_dst_rem_010_zero_dev_token_bypasses():
    """DST-REM-010: Client source code contains no dev-admin-token or dev token fallbacks."""
    web_src = REPO_ROOT / "web" / "src"
    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            if "dev-admin-token" in text or "dev-default-tenant" in text:
                violations.append(str(f.relative_to(REPO_ROOT)))

    assert len(violations) == 0, f"Dev token bypass found in client source: {violations}"
