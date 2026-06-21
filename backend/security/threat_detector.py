"""
Threat Detector
===============

Scans web requests and user inputs for heuristic indicators of injection attacks, XSS, and path traversal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .exceptions import ThreatDetectedError


class ThreatLevel(Enum):
    """Threat severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __ge__(self, other: ThreatLevel) -> bool:
        order = [ThreatLevel.LOW, ThreatLevel.MEDIUM, ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        return order.index(self) >= order.index(other)


@dataclass
class ThreatIndicator:
    """Represents a detected threat indicator."""

    indicator_type: str  # e.g., 'sql_injection', 'xss', 'path_traversal'
    description: str
    severity: ThreatLevel
    matched_pattern: str


class ThreatDetector:
    """
    Scans inputs and requests for common attack patterns.
    """

    SQLI_PATTERNS = [
        (re.compile(r"union\s+(all\s+)?select", re.IGNORECASE), "SQL injection: UNION SELECT clause"),
        (re.compile(r"select\s+.*\s+from", re.IGNORECASE), "SQL injection: SELECT FROM clause"),
        (re.compile(r"insert\s+into", re.IGNORECASE), "SQL injection: INSERT INTO statement"),
        (re.compile(r"drop\s+table", re.IGNORECASE), "SQL injection: DROP TABLE statement"),
        (re.compile(r"'\s*or\s*'\d+'\s*=\s*'\d+", re.IGNORECASE), "SQL injection: tautology OR condition"),
        (re.compile(r"--|/\*|\*/", re.IGNORECASE), "SQL injection: comment block"),
    ]

    XSS_PATTERNS = [
        (re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL), "XSS: script tag injection"),
        (re.compile(r"javascript\s*:", re.IGNORECASE), "XSS: javascript URI handler"),
        (re.compile(r"onerror\s*=|onload\s*=|onclick\s*=", re.IGNORECASE), "XSS: inline event handlers"),
        (re.compile(r"<iframe.*?>.*?</iframe>", re.IGNORECASE | re.DOTALL), "XSS: iframe injection"),
    ]

    TRAVERSAL_PATTERNS = [
        (re.compile(r"\.\./|\.\.\\"), "Path Traversal: relative path dots"),
        (re.compile(r"/etc/passwd|/etc/shadow|/etc/hosts", re.IGNORECASE), "Path Traversal: Unix system files"),
        (re.compile(r"c:\\windows|c:\\boot\.ini", re.IGNORECASE), "Path Traversal: Windows system paths"),
    ]

    def __init__(self) -> None:
        self.indicators: List[ThreatIndicator] = []

    def scan_text(self, text: str) -> List[ThreatIndicator]:
        """Scan a single block of text for malicious patterns."""
        detected = []
        if not text:
            return detected

        # Scan SQL injection patterns
        for pattern, desc in self.SQLI_PATTERNS:
            match = pattern.search(text)
            if match:
                detected.append(
                    ThreatIndicator(
                        indicator_type="sql_injection",
                        description=desc,
                        severity=ThreatLevel.HIGH,
                        matched_pattern=match.group(0),
                    )
                )

        # Scan XSS patterns
        for pattern, desc in self.XSS_PATTERNS:
            match = pattern.search(text)
            if match:
                detected.append(
                    ThreatIndicator(
                        indicator_type="xss",
                        description=desc,
                        severity=ThreatLevel.HIGH,
                        matched_pattern=match.group(0),
                    )
                )

        # Scan Path Traversal patterns
        for pattern, desc in self.TRAVERSAL_PATTERNS:
            match = pattern.search(text)
            if match:
                detected.append(
                    ThreatIndicator(
                        indicator_type="path_traversal",
                        description=desc,
                        severity=ThreatLevel.CRITICAL,
                        matched_pattern=match.group(0),
                    )
                )

        return detected

    def scan_request(
        self,
        path: str,
        query_params: Dict[str, Any],
        body: Optional[str] = None,
    ) -> List[ThreatIndicator]:
        """Scan request components (path, params, body) for threats."""
        detected = []

        # Scan path
        detected.extend(self.scan_text(path))

        # Scan query params
        for k, v in query_params.items():
            detected.extend(self.scan_text(str(k)))
            detected.extend(self.scan_text(str(v)))

        # Scan body
        if body:
            detected.extend(self.scan_text(body))

        return detected

    def check_threats(
        self,
        path: str,
        query_params: Dict[str, Any],
        body: Optional[str] = None,
        block_threshold: ThreatLevel = ThreatLevel.HIGH,
    ) -> List[ThreatIndicator]:
        """Scan request and raise ThreatDetectedError if any threat meets or exceeds threshold."""
        indicators = self.scan_request(path, query_params, body)
        for indicator in indicators:
            if indicator.severity >= block_threshold:
                raise ThreatDetectedError(
                    f"Threat detected: {indicator.description} (Severity: {indicator.severity.value})"
                )
        return indicators
