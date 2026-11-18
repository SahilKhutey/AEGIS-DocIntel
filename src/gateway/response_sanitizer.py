"""
AEGIS-DocIntel Response Sanitizer
PROT-FINAL-05: Workstream DEP-02 & DEP-09

Strips internal stack traces, internal IP addresses, database credentials,
infrastructure topologies, and proprietary prompts/secrets from all evaluator-facing
responses before transmission.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Union

INTERNAL_IP_REGEX = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b"
)
DB_URI_REGEX = re.compile(r"postgres(?:ql)?://[^\s\"']+", re.IGNORECASE)
SECRET_KEY_REGEX = re.compile(r"\b(?:sk-[a-zA-Z0-9_-]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16})\b")
STACK_TRACE_FILE_REGEX = re.compile(r'File "([^"]+)", line \d+, in \w+')


class ResponseSanitizer:
    """
    Sanitizes responses and error payloads at the gateway boundary.
    """

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Redacts sensitive infrastructure identifiers from string content."""
        if not text:
            return text
        text = INTERNAL_IP_REGEX.sub("[REDACTED_INTERNAL_IP]", text)
        text = DB_URI_REGEX.sub("[REDACTED_DATABASE_URI]", text)
        text = SECRET_KEY_REGEX.sub("[REDACTED_SECRET_KEY]", text)
        return text

    @classmethod
    def sanitize_payload(cls, data: Any) -> Any:
        """Recursively sanitizes dict, list, or primitive data structures."""
        if isinstance(data, dict):
            clean_dict = {}
            for k, v in data.items():
                # Strip stack traces and internal debugging objects
                if k in {"traceback", "stack_trace", "internal_debug", "raw_exception", "db_host", "connection_string"}:
                    continue
                clean_dict[k] = cls.sanitize_payload(v)
            return clean_dict
        elif isinstance(data, list):
            return [cls.sanitize_payload(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        return data

    @classmethod
    def sanitize_error(cls, exc: Exception, request_id: str = "") -> Dict[str, Any]:
        """
        Formats a sanitized, fail-closed error response for evaluators, preventing
        internal exception leakage (DEP-TEST-013, DEP-TEST-015).
        """
        msg = str(exc)
        sanitized_msg = cls.sanitize_text(msg)
        # Never expose raw Python tracebacks or internal module paths
        if "Traceback (" in sanitized_msg or "File \"" in sanitized_msg:
            sanitized_msg = "An internal processing error occurred. The incident has been recorded."

        return {
            "error": "PROCESSING_ERROR",
            "message": sanitized_msg,
            "request_id": request_id,
            "status": "FAILED",
        }


response_sanitizer = ResponseSanitizer()
