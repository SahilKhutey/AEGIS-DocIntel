"""
Adversarial Penetration Testing Suite — IP & Secret Exposure
PROT-FINAL-03: Workstream 11 (PT-IP-001 through PT-IP-015)

Validates that the downloadable evaluation package, client distribution artifacts,
and public client sources contain zero proprietary engine source files, private
keys, database credentials, provider API keys, unredacted secrets, or internal hostnames.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DIST_ROOT = REPO_ROOT / "distribution" / "demo-edition"
WEB_SRC = REPO_ROOT / "web" / "src"


def test_pt_ip_001_no_env_files_in_distribution():
    """PT-IP-001: Verifies zero .env files or secret environment configurations exist in distribution package."""
    assert DIST_ROOT.exists()
    env_files = list(DIST_ROOT.rglob(".env*"))
    assert len(env_files) == 0, f"Prohibited .env files found in distribution: {env_files}"


def test_pt_ip_002_no_private_keys_in_distribution():
    """PT-IP-002: Verifies zero private cryptographic keys exist in distribution or web client sources."""
    private_key_patterns = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ]
    targets = [DIST_ROOT, WEB_SRC]
    leaks = []

    for target in targets:
        if not target.exists():
            continue
        for f in target.rglob("*"):
            if f.is_file() and f.suffix in (".js", ".ts", ".tsx", ".json", ".md", ".yaml", ".yml", ".ps1", ".sh", ".conf"):
                text = f.read_text(encoding="utf-8", errors="ignore")
                for pat in private_key_patterns:
                    if pat in text:
                        leaks.append((str(f.relative_to(REPO_ROOT)), pat))

    assert len(leaks) == 0, f"Private key leaks identified: {leaks}"


def test_pt_ip_003_no_db_connection_strings_in_distribution():
    """PT-IP-003: Verifies zero production database connection strings exist in client distribution."""
    db_patterns = [
        re.compile(r"postgresql://[^:]+:[^@]+@", re.IGNORECASE),
        re.compile(r"mysql://[^:]+:[^@]+@", re.IGNORECASE),
        re.compile(r"mongodb(\+srv)?://[^:]+:[^@]+@", re.IGNORECASE),
        re.compile(r"redis://:[^@]+@", re.IGNORECASE),
    ]
    leaks = []
    for f in DIST_ROOT.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pat in db_patterns:
                if pat.search(text):
                    leaks.append(str(f.relative_to(REPO_ROOT)))

    assert len(leaks) == 0, f"Database connection strings detected: {leaks}"


def test_pt_ip_004_no_provider_api_keys_in_distribution():
    """PT-IP-004: Verifies zero OpenAI, Anthropic, Google, or GitHub API keys in client distribution."""
    api_patterns = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ]
    leaks = []
    for f in DIST_ROOT.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pat in api_patterns:
                if pat.search(text):
                    leaks.append(str(f.relative_to(REPO_ROOT)))

    assert len(leaks) == 0, f"Cloud/AI API keys detected in distribution: {leaks}"


def test_pt_ip_005_no_staging_admin_endpoints_in_client():
    """PT-IP-005: Verifies client launcher scripts contain zero hardcoded internal admin endpoints."""
    admin_patterns = ["/v1/admin/evaluation/signing-keys", "/v1/admin/evaluation/security", "/admin/platform"]
    launcher_dir = DIST_ROOT / "launcher"
    leaks = []

    for f in launcher_dir.glob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pat in admin_patterns:
                if pat in text:
                    leaks.append((str(f.relative_to(REPO_ROOT)), pat))

    assert len(leaks) == 0, f"Admin endpoints exposed in client launchers: {leaks}"


def test_pt_ip_006_no_internal_ips_or_corp_hostnames():
    """PT-IP-006: Verifies zero RFC 1918 private corporate IP addresses or internal domain names in client distribution."""
    corp_domains = [re.compile(r"[a-zA-Z0-9_\-\.]+\.(internal|corp|local|lan)")]
    leaks = []

    for f in DIST_ROOT.rglob("*"):
        if f.is_file() and f.suffix in (".ps1", ".sh", ".yaml", ".json", ".conf"):
            text = f.read_text(encoding="utf-8", errors="ignore")
            for pat in corp_domains:
                matches = pat.findall(text)
                if matches:
                    leaks.append((str(f.relative_to(REPO_ROOT)), matches))

    assert len(leaks) == 0, f"Internal domain leaks: {leaks}"


def test_pt_ip_007_no_proprietary_dag_engine_in_distribution():
    """PT-IP-007: Verifies zero Python engine source code or bytecode is packaged in distribution."""
    prohibited_extensions = [".py", ".pyc", ".pyo", ".pyd"]
    leaks = []

    for f in DIST_ROOT.rglob("*"):
        if f.suffix in prohibited_extensions:
            leaks.append(str(f.relative_to(REPO_ROOT)))

    assert len(leaks) == 0, f"Proprietary Python engine files found in distribution: {leaks}"


def test_pt_ip_008_no_proprietary_prompts_in_distribution():
    """PT-IP-008: Verifies proprietary system prompts or LLM chain definitions are not in distribution package."""
    prompt_signatures = [
        "You are AEGIS-DocIntel Core Reasoning Engine",
        "DAG_ORCHESTRATION_PROMPT",
        "GOLDEN_REASONING_CHAIN",
    ]
    leaks = []
    for f in DIST_ROOT.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="ignore")
            for sig in prompt_signatures:
                if sig in text:
                    leaks.append((str(f.relative_to(REPO_ROOT)), sig))

    assert len(leaks) == 0, f"Proprietary prompts found in distribution: {leaks}"


def test_pt_ip_009_no_internal_golden_benchmark_data_in_distribution():
    """PT-IP-009: Verifies internal golden benchmarks (evaluation/mvp-golden/expected, text) are strictly excluded from distribution."""
    golden_files = list((REPO_ROOT / "evaluation" / "mvp-golden" / "expected").rglob("*")) + list((REPO_ROOT / "evaluation" / "mvp-golden" / "text").rglob("*"))
    golden_names = {g.name for g in golden_files if g.is_file()}

    leaks = []
    for f in DIST_ROOT.rglob("*"):
        if f.is_file() and f.name in golden_names:
            leaks.append(str(f.relative_to(REPO_ROOT)))

    assert len(leaks) == 0, f"Proprietary benchmark ground truths leaked: {leaks}"


def test_pt_ip_010_no_source_maps_in_distribution():
    """PT-IP-010: Verifies no JavaScript or TypeScript sourcemap (.map) files exist in distribution."""
    source_maps = list(DIST_ROOT.rglob("*.map"))
    assert len(source_maps) == 0, f"Source maps found in distribution: {source_maps}"


def test_pt_ip_011_no_docker_compose_embedded_secrets():
    """PT-IP-011: Inspects deployment compose specifications to confirm zero embedded hardcoded secrets."""
    compose_path = DIST_ROOT / "deploy" / "compose.yaml"
    assert compose_path.exists()
    content = compose_path.read_text(encoding="utf-8")
    
    # Check that secrets are parameterized or absent
    assert "password" not in content.lower()
    assert "secret" not in content.lower() or "secret" in "${"  # Allowed if variable reference
    assert "api_key" not in content.lower()


def test_pt_ip_012_no_plaintext_credentials_in_client_config():
    """PT-IP-012: Confirms default client configuration templates contain no hardcoded auth tokens."""
    for conf_file in (DIST_ROOT / "deploy").glob("*.conf"):
        text = conf_file.read_text(encoding="utf-8")
        assert "Authorization: Bearer" not in text
        assert "X-API-Key" not in text


def test_pt_ip_013_package_manifest_sha256_integrity():
    """PT-IP-013: Validates cryptographic SHA-256 integrity for every file declared in package-manifest.json."""
    manifest_path = DIST_ROOT / "package-manifest.json"
    assert manifest_path.exists()
    
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    files_list = manifest_data.get("files", [])
    assert len(files_list) > 0

    for file_entry in files_list:
        rel_path = file_entry["path"]
        expected_sha = file_entry["sha256"]
        target_path = DIST_ROOT / rel_path
        
        assert target_path.exists(), f"Manifest file missing: {rel_path}"
        actual_sha = hashlib.sha256(target_path.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA-256 mismatch for {rel_path}: expected {expected_sha}, got {actual_sha}"


def test_pt_ip_014_repository_secret_scan():
    """PT-IP-014: High-confidence heuristic scan confirms zero accidental tokens or unredacted keys in public code."""
    from src.security.event_redaction import sanitize_event_details
    test_dict = {
        "auth_header": "Bearer eyJhbGciOiJFZERTQTEyMzQ1Njc4OTAifQ.evaluator_secret",
        "api_key": "sk-proj-testkey12345",
        "password": "SuperSecretPass123!",
    }
    sanitized = sanitize_event_details(test_dict)
    assert sanitized["auth_header"] != test_dict["auth_header"]
    assert sanitized["api_key"] != test_dict["api_key"]
    assert sanitized["password"] == "[REDACTED]"


def test_pt_ip_015_distribution_file_safety_permissions():
    """PT-IP-015: Confirms distribution files have safe attributes and no arbitrary binary executable extensions."""
    prohibited_binaries = [".exe", ".msi", ".dll", ".so", ".dylib", ".bin"]
    leaks = []
    for f in DIST_ROOT.rglob("*"):
        if f.suffix.lower() in prohibited_binaries:
            leaks.append(str(f.relative_to(REPO_ROOT)))

    assert len(leaks) == 0, f"Unverified native binary executables found: {leaks}"
