"""
AEGIS-DocIntel Secrets & Key Management Engine
PROT-FINAL-05: Workstream DEP-07

Handles secure secret loading, environment separation, and key inventory lifecycle:
- Secret resolution from Docker secret files (/run/secrets/*) or environment variables
- Strict rejection of staging credentials in production runtime (DEP-TEST-007)
- Key inventory purpose segregation (JWT != License signing != Service HMAC)
- Zero plaintext secret leakage into logs or client artifacts
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("aegis.infrastructure.secrets")

SECRET_PURPOSES = {
    "jwt_signing_key": "Protected identity authentication infrastructure",
    "license_signing_key": "Protected license service",
    "activation_hmac_key": "Evaluator activation challenge verification",
    "internal_service_secret": "Gateway-to-Engine HMAC-SHA256 service authentication",
    "database_password": "PostgreSQL transactional database authentication",
    "openai_api_key": "Outbound OpenAI model adapter",
    "anthropic_api_key": "Outbound Anthropic model adapter",
    "tls_private_key": "Edge reverse proxy TLS termination",
}


class SecretResolutionError(Exception):
    pass


class SecretManager:
    """
    Manages production and staging secret resolution.
    """

    def __init__(self, current_env: str = "production"):
        self._current_env = current_env

    def set_environment(self, env: str) -> None:
        self._current_env = env

    def resolve_secret(self, key_name: str, default: Optional[str] = None) -> str:
        """
        Resolves secret from:
        1. ${KEY_NAME}_FILE path if defined
        2. ${KEY_NAME} direct environment variable
        3. default fallback
        """
        file_var = f"{key_name}_FILE"
        file_path = os.getenv(file_var)

        secret_val: Optional[str] = None
        if file_path and os.path.exists(file_path):
            try:
                secret_val = Path(file_path).read_text(encoding="utf-8").strip()
            except Exception as exc:
                logger.warning("Failed to read secret file %s: %s", file_path, exc)

        if not secret_val:
            secret_val = os.getenv(key_name, default)

        if not secret_val:
            raise SecretResolutionError(f"Mandatory secret '{key_name}' could not be resolved.")

        # DEP-TEST-007: Staging credential used in production must be rejected
        if self._current_env == "production" and ("staging" in secret_val.lower() or "test" in secret_val.lower()):
            raise SecretResolutionError(
                f"Security violation: Staging or test secret detected in production environment for '{key_name}'."
            )

        return secret_val

    def validate_key_separation(self, keys: Dict[str, str]) -> bool:
        """
        Validates that signing keys are separated by purpose.
        A release-signing key must never be used as a JWT or license key.
        """
        seen_values: Dict[str, str] = {}
        for purpose, val in keys.items():
            if val in seen_values:
                raise SecretResolutionError(
                    f"Key purpose violation: Key for '{purpose}' is identical to key for '{seen_values[val]}'."
                )
            seen_values[val] = purpose
        return True

    def get_inventory(self) -> Dict[str, Any]:
        """Returns the non-sensitive inventory of managed secrets and their trust boundaries."""
        return {
            purpose: {
                "description": desc,
                "client_accessible": False,
                "storage_mechanism": "Docker Secrets / KMS / Secret Manager",
            }
            for purpose, desc in SECRET_PURPOSES.items()
        }


secret_manager = SecretManager()
