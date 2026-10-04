"""
Export Verification
===================

Pre-export validation of context integrity:
- Citation presence
- Conservation law check
- Confidence threshold
- Hallucination indicators
- Required fields present
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import VerificationError
from .universal_exporter import UniversalExportObject


@dataclass
class VerificationResult:
    """Result of pre-export verification."""

    is_valid: bool
    confidence: float
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "confidence": round(self.confidence, 4),
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
        }


class ExportVerifier:
    """
    Pre-export verification.

    Validates:
        - Required fields are present
        - Confidence meets threshold
        - Citations are not empty (when required)
        - Content is not empty
        - Token budget is respected
    """

    def __init__(
        self,
        min_confidence: float = 0.5,
        require_citations: bool = False,
        require_summary: bool = True,
        max_tokens: Optional[int] = None,
    ) -> None:
        if not (0 <= min_confidence <= 1):
            raise ValueError("min_confidence must be in [0, 1].")
        self.min_confidence = min_confidence
        self.require_citations = require_citations
        self.require_summary = require_summary
        self.max_tokens = max_tokens

    def verify(
        self,
        ueo: UniversalExportObject,
    ) -> VerificationResult:
        """
        Run all verification checks.
        """
        passed: List[str] = []
        failed: List[str] = []
        warnings: List[str] = []

        # required fields
        if ueo.system is None:
            failed.append("missing_system")
        else:
            passed.append("system_present")

        if ueo.context is None or ueo.context == "":
            failed.append("missing_context")
        else:
            passed.append("context_present")

        if self.require_summary and (ueo.summary is None or ueo.summary == ""):
            failed.append("missing_summary")
        elif ueo.summary:
            passed.append("summary_present")

        # citations
        if self.require_citations and not ueo.citations:
            failed.append("missing_citations")
        elif ueo.citations:
            passed.append("citations_present")

        # confidence
        if ueo.confidence < self.min_confidence:
            failed.append("low_confidence")
        else:
            passed.append("confidence_ok")

        # token budget
        if self.max_tokens is not None and ueo.total_tokens > self.max_tokens:
            failed.append("token_budget_exceeded")
        else:
            passed.append("tokens_ok")

        # hallucination heuristic: very high confidence + empty content
        if ueo.confidence > 0.9 and (
            not ueo.context or len(ueo.context) < 20
        ):
            warnings.append("high_confidence_low_content")

        # conservation heuristic
        if ueo.metadata.get("conservation_error", 0) > 0.1:
            warnings.append("high_conservation_error")

        confidence = (
            ueo.confidence if ueo.confidence is not None else 0.0
        )
        is_valid = len(failed) == 0
        return VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            checks_passed=passed,
            checks_failed=failed,
            warnings=warnings,
        )

    def verify_or_raise(self, ueo: UniversalExportObject) -> VerificationResult:
        """Verify and raise on failure."""
        result = self.verify(ueo)
        if not result.is_valid:
            raise VerificationError(
                f"Verification failed: {result.checks_failed}"
            )
        return result