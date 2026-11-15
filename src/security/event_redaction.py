"""
AEGIS-DocIntel Security Event Redaction Engine (PROT-04 WP-04.08)
Enforces strict data minimization by masking credentials, private keys, and document payloads.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Union

SENSITIVE_KEY_PATTERNS: Set[str] = {
    "password", "secret", "token", "access_token", "refresh_token",
    "private_key", "api_key", "activation_code", "recovery_code",
    "authorization", "cookie", "set-cookie", "document_content",
    "text", "llm_prompt", "prompt", "raw_payload"
}

REDACTION_REGEXES = [
    (re.compile(r"AEGIS-EVAL-[A-Z0-9]{4}-[A-Z0-9]{4}", re.IGNORECASE), "AEGIS-EVAL-****-****"),
    (re.compile(r"REC-[A-Z0-9]{4}-[A-Z0-9]{4}", re.IGNORECASE), "REC-****-****"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_.]+", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"aegis_eval_(?:at|rt|ws_tkt)_[A-Za-z0-9\-_]+", re.IGNORECASE), "[REDACTED_AEGIS_TOKEN]"),
    (re.compile(r"eyJ[A-Za-z0-9\-_.]+\.[A-Za-z0-9\-_.]+\.[A-Za-z0-9\-_.]+"), "[REDACTED_JWT]"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


def contains_sensitive_data(val: Any) -> bool:
    """Checks whether arbitrary data contains unredacted credentials or private keys."""
    if isinstance(val, str):
        if any(tok in val.lower() for tok in ["private key-----", "bearer eyj", "aegis_eval_rt_"]):
            return True
        for pattern, _ in REDACTION_REGEXES:
            if pattern.search(val):
                return True
    elif isinstance(val, dict):
        for k, v in val.items():
            if str(k).lower() in SENSITIVE_KEY_PATTERNS:
                return True
            if contains_sensitive_data(v):
                return True
    elif isinstance(val, (list, tuple, set)):
        return any(contains_sensitive_data(item) for item in val)
    return False


def redact_text(text: str) -> str:
    """Masks secret substrings within plain text."""
    redacted = text
    for pattern, replacement in REDACTION_REGEXES:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def sanitize_event_details(details: Union[Dict[str, Any], Any], reject_if_secret: bool = False) -> Dict[str, Any]:
    """
    Recursively scrubs metadata dictionaries, masking credentials and stripping prohibited payloads.
    If reject_if_secret=True and an unredacted secret is found, raises ValueError.
    """
    if not isinstance(details, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    for k, v in details.items():
        k_lower = str(k).lower()
        if k_lower in SENSITIVE_KEY_PATTERNS:
            if reject_if_secret:
                raise ValueError(f"Prohibited sensitive key '{k}' detected in security event details.")
            sanitized[k] = "[REDACTED]"
            continue

        if isinstance(v, str):
            if reject_if_secret and contains_sensitive_data(v):
                raise ValueError(f"Sensitive credential detected in field '{k}'.")
            sanitized[k] = redact_text(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_event_details(v, reject_if_secret=reject_if_secret)
        elif isinstance(v, (list, tuple)):
            sanitized[k] = [
                redact_text(item) if isinstance(item, str) else
                sanitize_event_details(item, reject_if_secret=reject_if_secret) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            sanitized[k] = v

    return sanitized
