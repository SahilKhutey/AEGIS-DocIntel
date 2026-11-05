"""
aegis.security.injection_guard
==============================
Defensive analyzer detecting prompt injection, instruction override,
and context leakage attacks embedded in document text.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from pydantic import BaseModel, Field


class InjectionFinding(BaseModel):
    category: str
    pattern_matched: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    description: str


class InjectionScanResult(BaseModel):
    is_safe: bool
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    findings: List[InjectionFinding] = Field(default_factory=list)


class PromptInjectionGuard:
    """Analyzes raw text for adversarial prompt injection signatures."""

    DIRECT_OVERRIDE_PATTERNS = [
        (r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b", "Direct instruction override"),
        (r"\bdisregard\s+(all\s+)?(previous|prior|above)\s+prompts?\b", "Direct prompt override"),
        (r"\byou\s+are\s+now\s+(in\s+)?(developer|dan|god|jailbreak)\s+mode\b", "Persona hijack"),
        (r"\bfrom\s+now\s+on,\s+you\s+must\s+act\s+as\b", "Behavioral override"),
        (r"\bdo\s+anything\s+now\b", "DAN jailbreak attempt"),
    ]

    DELIMITER_SPOOFING_PATTERNS = [
        (r"<\|im_start\|>", "ChatML delimiter injection"),
        (r"<\|im_end\|>", "ChatML delimiter injection"),
        (r"\[SYSTEM\]\s*:", "System prompt header spoofing"),
        (r"\[INST\]", "Llama instruction delimiter injection"),
        (r"---+\s*(BEGIN|END)\s+SYSTEM\s+PROMPT\s*---+", "Synthetic system barrier spoofing"),
    ]

    EXFILTRATION_PATTERNS = [
        (r"\boutput\s+(the\s+)?(system\s+prompt|context\s+window|hidden\s+instructions)\b", "Internal prompt extraction"),
        (r"\bprint\s+(the\s+)?(api[_\-\s]?key|jwt|secret|token)\b", "Credential exfiltration probe"),
        (r"\bexfiltrate\s+to\s+https?://\b", "Remote exfiltration instruction"),
    ]

    @classmethod
    def scan_text(cls, text: str) -> InjectionScanResult:
        if not text:
            return InjectionScanResult(is_safe=True, risk_score=0.0, findings=[])

        findings: List[InjectionFinding] = []
        norm = text.lower()

        # Check direct override
        for pat, desc in cls.DIRECT_OVERRIDE_PATTERNS:
            if re.search(pat, norm, re.IGNORECASE):
                findings.append(
                    InjectionFinding(
                        category="DIRECT_OVERRIDE",
                        pattern_matched=pat,
                        severity="HIGH",
                        description=desc,
                    )
                )

        # Check delimiter spoofing
        for pat, desc in cls.DELIMITER_SPOOFING_PATTERNS:
            if re.search(pat, text, re.IGNORECASE):
                findings.append(
                    InjectionFinding(
                        category="DELIMITER_SPOOFING",
                        pattern_matched=pat,
                        severity="HIGH",
                        description=desc,
                    )
                )

        # Check exfiltration
        for pat, desc in cls.EXFILTRATION_PATTERNS:
            if re.search(pat, norm, re.IGNORECASE):
                findings.append(
                    InjectionFinding(
                        category="EXFILTRATION_PROBE",
                        pattern_matched=pat,
                        severity="MEDIUM",
                        description=desc,
                    )
                )

        if not findings:
            return InjectionScanResult(is_safe=True, risk_score=0.0, findings=[])

        high_count = sum(1 for f in findings if f.severity == "HIGH")
        med_count = sum(1 for f in findings if f.severity == "MEDIUM")
        score = min(1.0, high_count * 0.5 + med_count * 0.25)

        return InjectionScanResult(
            is_safe=len(findings) == 0,
            risk_score=round(score, 2),
            findings=findings,
        )
