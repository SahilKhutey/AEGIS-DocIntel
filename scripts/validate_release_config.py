#!/usr/bin/env python3
"""
scripts/validate_release_config.py
==================================
Phase 3.5 Production Readiness & Release Qualification:
Validates deployment configuration, environment variables, authentication invariants,
storage security, CORS policy, and external data transfer boundaries.

Usage:
    python scripts/validate_release_config.py [--env production] [--output artifacts/phase3/release-config-validation.txt]
    python scripts/validate_release_config.py --json

Exit codes:
    0 = All release configuration checks passed
    1 = One or more release configuration checks failed
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.settings import ConfigurationError, RuntimeSettings, load_runtime_settings


def check_configuration(target_env: str = "production") -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Run itemized configuration checks against runtime settings for the specified environment.
    """
    checks: List[Dict[str, Any]] = []

    # Temporarily force AEGIS_ENVIRONMENT if not matching target_env
    orig_env = os.environ.get("AEGIS_ENVIRONMENT")
    os.environ["AEGIS_ENVIRONMENT"] = target_env

    try:
        settings: RuntimeSettings = load_runtime_settings(validate_production=(target_env in {"staging", "production"}))
        load_error = None
    except ConfigurationError as e:
        settings = None
        load_error = str(e)
    finally:
        if orig_env is not None:
            os.environ["AEGIS_ENVIRONMENT"] = orig_env
        else:
            os.environ.pop("AEGIS_ENVIRONMENT", None)

    # 1. Setting Loading Invariant
    if load_error is not None:
        checks.append({
            "check": "production_settings_load",
            "passed": False,
            "severity": "CRITICAL",
            "message": f"Runtime configuration rejected: {load_error}",
        })
        return False, checks

    checks.append({
        "check": "production_settings_load",
        "passed": True,
        "severity": "INFO",
        "message": f"Configuration loaded successfully for environment '{settings.environment}'",
    })

    # 2. Database Persistence Invariant
    db_path = settings.database_path
    if not db_path or db_path == ":memory:":
        checks.append({
            "check": "database_persistence",
            "passed": False,
            "severity": "CRITICAL",
            "message": f"In-memory SQLite database '{db_path}' is forbidden in release configuration",
        })
    else:
        parent = Path(db_path).parent
        parent_writable = os.access(parent, os.W_OK) if parent.exists() else True
        checks.append({
            "check": "database_persistence",
            "passed": parent_writable,
            "severity": "CRITICAL" if not parent_writable else "INFO",
            "message": f"Database file path configured: '{db_path}' (directory writable: {parent_writable})",
        })

    # 3. CORS Policy Invariant
    if "*" in settings.cors_origins:
        checks.append({
            "check": "cors_wildcard_forbidden",
            "passed": False,
            "severity": "HIGH",
            "message": "Wildcard origin '*' present in AEGIS_CORS_ORIGINS",
        })
    else:
        checks.append({
            "check": "cors_wildcard_forbidden",
            "passed": True,
            "severity": "INFO",
            "message": f"CORS origins restricted to: {settings.cors_origins}",
        })

    # 4. Authentication Provider Invariant
    has_jwt = bool(settings.jwt_public_key or settings.jwt_public_key_path)
    has_api_keys = bool(settings.api_keys)
    if target_env in {"staging", "production"} and not (has_jwt or has_api_keys):
        checks.append({
            "check": "auth_provider_configured",
            "passed": False,
            "severity": "CRITICAL",
            "message": "Neither JWT public key nor API keys are configured for authentication",
        })
    else:
        auth_mechanisms = []
        if has_jwt:
            auth_mechanisms.append("JWT (RSA/EdDSA)")
        if has_api_keys:
            auth_mechanisms.append("API Keys (SHA-256 hashed)")
        checks.append({
            "check": "auth_provider_configured",
            "passed": True,
            "severity": "INFO",
            "message": f"Active authentication mechanisms: {', '.join(auth_mechanisms)}",
        })

    # 5. External Data Transfer & LLM Policy
    if target_env in {"staging", "production"} and settings.llm_provider == "mock":
        checks.append({
            "check": "llm_provider_policy",
            "passed": False,
            "severity": "CRITICAL",
            "message": "Mock LLM provider is active in production mode",
        })
    elif settings.llm_provider in {"openai", "anthropic", "google"} and not settings.allow_external_llm:
        checks.append({
            "check": "llm_provider_policy",
            "passed": False,
            "severity": "HIGH",
            "message": f"External LLM '{settings.llm_provider}' configured without explicit authorization",
        })
    else:
        checks.append({
            "check": "llm_provider_policy",
            "passed": True,
            "severity": "INFO",
            "message": f"LLM provider '{settings.llm_provider}' conforms to data transfer policy",
        })

    # 6. Upload Size Safety Limits
    if settings.max_upload_bytes > 500 * 1024 * 1024:
        checks.append({
            "check": "upload_limit_safety",
            "passed": False,
            "severity": "MEDIUM",
            "message": f"Upload limit {settings.max_upload_bytes} exceeds recommended maximum of 500MB",
        })
    elif settings.max_upload_bytes < 1024:
        checks.append({
            "check": "upload_limit_safety",
            "passed": False,
            "severity": "HIGH",
            "message": f"Upload limit {settings.max_upload_bytes} is below minimum allowed 1024 bytes",
        })
    else:
        checks.append({
            "check": "upload_limit_safety",
            "passed": True,
            "severity": "INFO",
            "message": f"Max upload limit safely bounded: {settings.max_upload_bytes // (1024 * 1024)} MB",
        })

    # 7. Telemetry & Metrics Safety
    checks.append({
        "check": "telemetry_privacy",
        "passed": settings.pseudonymize_telemetry,
        "severity": "HIGH" if not settings.pseudonymize_telemetry else "INFO",
        "message": f"Pseudonymize telemetry: {settings.pseudonymize_telemetry}",
    })

    all_passed = all(c["passed"] for c in checks)
    return all_passed, checks


def load_env_file(filepath: Path) -> None:
    """Parse a simple KEY=VALUE .env file and populate os.environ."""
    if not filepath.exists():
        raise FileNotFoundError(f"Specified env-file not found: {filepath}")
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip("'\"")
        os.environ[key] = val


def main() -> int:
    parser = argparse.ArgumentParser(description="AEGIS-DocIntel Release Configuration Validator")
    parser.add_argument("--env", default="production", choices=["development", "test", "staging", "production"],
                        help="Target deployment environment (default: production)")
    parser.add_argument("--env-file", type=Path, help="Optional path to .env file to load into environment")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output", type=Path, help="File path to save the validation report")
    args = parser.parse_args()

    if args.env_file:
        load_env_file(args.env_file)

    passed, checks = check_configuration(target_env=args.env)

    summary = {
        "environment": args.env,
        "status": "PASS" if passed else "FAIL",
        "total_checks": len(checks),
        "passed_checks": sum(1 for c in checks if c["passed"]),
        "failed_checks": sum(1 for c in checks if not c["passed"]),
        "checks": checks,
    }

    if args.json:
        output_str = json.dumps(summary, indent=2)
    else:
        lines = [
            "=" * 60,
            f"AEGIS-DocIntel Release Configuration Validation: [{args.env.upper()}]",
            "=" * 60,
        ]
        for c in checks:
            tag = "[PASS]" if c["passed"] else f"[{c['severity']} FAIL]"
            lines.append(f"{tag:<14} {c['check']}: {c['message']}")
        lines.append("-" * 60)
        lines.append(f"Result: {summary['status']} ({summary['passed_checks']}/{summary['total_checks']} checks passed)")
        lines.append("=" * 60)
        output_str = "\n".join(lines)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_str, encoding="utf-8")
        print(f"Report written to: {args.output}")

    print(output_str)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
