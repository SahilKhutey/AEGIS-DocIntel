"""
Consolidated Security Audit: Distribution Artifact Inspection & Secret Scan (SEC-001, SEC-002, SEC-017, SEC-020)
"""

from pathlib import Path
import re
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_dist_001_no_private_keys_in_client_source():
    """SEC-001.1: Verification confirms zero private key blocks in web distribution files."""
    forbidden_key_markers = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ]
    web_src = ROOT / "web" / "src"
    assert web_src.exists()

    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx", ".json", ".html", ".css"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            for marker in forbidden_key_markers:
                if marker in content:
                    violations.append((str(f.relative_to(ROOT)), marker))

    assert len(violations) == 0, f"Private key markers found: {violations}"


def test_dist_002_no_provider_api_keys_in_client_source():
    """SEC-002.1: Verification confirms zero foundation model API credentials in client source."""
    api_key_regexes = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),  # OpenAI
        re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"),  # Google API
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),  # GitHub token
    ]
    web_src = ROOT / "web" / "src"
    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx", ".json", ".html"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            for rgx in api_key_regexes:
                matches = rgx.findall(content)
                if matches:
                    violations.append((str(f.relative_to(ROOT)), matches))

    assert len(violations) == 0, f"Provider API keys found in client source: {violations}"


def test_dist_003_no_development_tokens_in_client_source():
    """SEC-001.2: Verification confirms zero dev-admin-token or mock tokens in client source."""
    web_src = ROOT / "web" / "src"
    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".js", ".jsx", ".ts", ".tsx", ".json"):
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "dev-admin-token" in content or "dev-default-tenant" in content:
                violations.append(str(f.relative_to(ROOT)))

    assert len(violations) == 0, f"Development bypass tokens found in client source: {violations}"


def test_dist_004_sensitive_data_redaction_in_security_events():
    """SEC-017.1: Security events strictly redact bearer tokens, private keys, and passwords."""
    from src.security.event_redaction import sanitize_event_details

    unredacted = {
        "authorization": "Bearer eyJhbGciOiJFZERTQTEyMzQ1Njc4OTAifQ.evaluator_secret",
        "api_key": "sk-proj-super-secret-key-12345",
        "password": "db_password_top_secret",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg...\n-----END PRIVATE KEY-----",
        "log_excerpt": "Failed connect with Bearer test_token_xyz and -----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg...\n-----END PRIVATE KEY-----",
        "safe_counter": 10,
    }
    redacted = sanitize_event_details(unredacted)

    assert redacted["authorization"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["private_key"] == "[REDACTED]"
    assert "[REDACTED_TOKEN]" in redacted["log_excerpt"]
    assert "[REDACTED_PRIVATE_KEY]" in redacted["log_excerpt"]
    assert redacted["safe_counter"] == 10


def test_dist_005_configuration_manifest_identifiable():
    """SEC-020.1: Release configuration manifest contains reproducible cryptographic algorithms."""
    from services.evaluation_gateway.license import CANONICAL_PRODUCT
    from services.evaluation_gateway.signing_key_registry import CANONICAL_ALGORITHM
    assert CANONICAL_PRODUCT == "AEGIS_PROTECTED_EVALUATION"
    assert CANONICAL_ALGORITHM == "EdDSA"
