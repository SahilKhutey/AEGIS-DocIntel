"""
Fact Verification
==================

Verifies factual claims in AI responses against a knowledge base.

Approach:
    1. Extract atomic claims (sentences with factual assertions)
    2. Normalize claims
    3. Match against source knowledge base
    4. Score each claim (SUPPORTED / CONTRADICTED / UNVERIFIED)

Mathematical Foundation:
    Fact accuracy:
        FA = |supported_claims| / |total_claims|

    Claim confidence:
        CC(c) = max similarity(c, s) for s in knowledge_base
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .exceptions import FactMismatchError


class FactStatus(Enum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNVERIFIED = "unverified"
    PARTIALLY_SUPPORTED = "partially_supported"


@dataclass
class FactClaim:
    """A single factual claim extracted from the response."""

    claim: str
    status: FactStatus
    confidence: float
    matched_source: Optional[str] = None
    contradictions: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "claim": self.claim,
            "status": self.status.value,
            "confidence": round(self.confidence, 4),
            "matched_source": self.matched_source,
            "contradictions": self.contradictions,
            "evidence": self.evidence,
        }


@dataclass
class FactCheckResult:
    """Result of fact verification."""

    total_claims: int
    supported_claims: int
    contradicted_claims: int
    unverified_claims: int
    partially_supported_claims: int
    accuracy: float
    claims: List[FactClaim] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_claims": self.total_claims,
            "supported_claims": self.supported_claims,
            "contradicted_claims": self.contradicted_claims,
            "unverified_claims": self.unverified_claims,
            "partially_supported_claims": self.partially_supported_claims,
            "accuracy": round(self.accuracy, 4),
            "claims": [c.to_dict() for c in self.claims],
            "issues": self.issues,
        }


class FactVerifier:
    """
    Verify factual claims using a knowledge base.

    Knowledge base structure:
        {
            "entity.property": ["value1", "value2"],
            "fact_key": "fact_statement",
            ...
        }
    """

    CLAIM_PATTERNS = [
        re.compile(r"[A-Z][^.!?]*\bis\s+[^.!?]*[.!?]"),
        re.compile(r"[A-Z][^.!?]*\bare\s+[^.!?]*[.!?]"),
        re.compile(r"[A-Z][^.!?]*\bwas\s+[^.!?]*[.!?]"),
        re.compile(r"\d+(?:\.\d+)?%[^.!?]*[.!?]"),
    ]

    def __init__(
        self,
        knowledge_base: Optional[Dict[str, Any]] = None,
        fuzzy_threshold: float = 0.75,
    ) -> None:
        self.knowledge_base = knowledge_base or {}
        self.fuzzy_threshold = fuzzy_threshold

    def verify(
        self,
        response_text: str,
        knowledge_base: Optional[Dict[str, Any]] = None,
    ) -> FactCheckResult:
        """
        Verify factual claims in `response_text`.

        Parameters
        ----------
        response_text : str
        knowledge_base : Optional[Dict]
            Override the instance knowledge_base.
        """
        kb = knowledge_base if knowledge_base is not None else self.knowledge_base
        claims = self._extract_claims(response_text)
        if not claims:
            return FactCheckResult(
                total_claims=0,
                supported_claims=0,
                contradicted_claims=0,
                unverified_claims=0,
                partially_supported_claims=0,
                accuracy=1.0,
                issues=["no_claims_found"],
            )

        verified: List[FactClaim] = []
        supported = 0
        contradicted = 0
        unverified = 0
        partial = 0

        for claim in claims:
            fact = self._verify_claim(claim, kb)
            verified.append(fact)
            if fact.status == FactStatus.SUPPORTED:
                supported += 1
            elif fact.status == FactStatus.CONTRADICTED:
                contradicted += 1
            elif fact.status == FactStatus.PARTIALLY_SUPPORTED:
                partial += 1
            else:
                unverified += 1

        total = len(claims)
        accuracy = (supported + 0.5 * partial) / max(total, 1)
        issues: List[str] = []
        if contradicted > 0:
            issues.append(f"{contradicted}_contradicted_facts")
        if unverified > total * 0.5:
            issues.append("majority_unverified")

        return FactCheckResult(
            total_claims=total,
            supported_claims=supported,
            contradicted_claims=contradicted,
            unverified_claims=unverified,
            partially_supported_claims=partial,
            accuracy=accuracy,
            claims=verified,
            issues=issues,
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Extract atomic claims from text."""
        # split by sentence
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        claims = []
        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue
            # skip questions
            if sent.endswith("?"):
                continue
            # skip imperatives
            if sent.lower().startswith(("please", "consider", "let ")):
                continue
            # has a factual assertion indicator
            has_assertion = any(re.search(p, sent) for p in self.CLAIM_PATTERNS)
            # has a number / proper noun (heuristic for factual)
            has_data = bool(re.search(r"\d", sent)) or any(
                w[0].isupper() for w in sent.split() if len(w) > 1
            )
            if has_assertion or has_data:
                claims.append(sent)
        return claims

    def _verify_claim(
        self,
        claim: str,
        kb: Dict[str, Any],
    ) -> FactClaim:
        """Verify a single claim against the knowledge base."""
        if not kb:
            return FactClaim(
                claim=claim,
                status=FactStatus.UNVERIFIED,
                confidence=0.5,
                evidence=[],
            )
        # exact / fuzzy match in kb
        best_match: Optional[str] = None
        best_score = 0.0
        for key, value in kb.items():
            # build text representation
            if isinstance(value, list):
                value_text = " ".join(str(v) for v in value)
            else:
                value_text = str(value)
            key_text = f"{key}: {value_text}"
            score = self._text_similarity(claim, key_text)
            if score > best_score:
                best_score = score
                best_match = key_text

        if best_match is None or best_score < 0.3:
            return FactClaim(
                claim=claim,
                status=FactStatus.UNVERIFIED,
                confidence=0.5,
                evidence=[],
            )
        if best_score >= self.fuzzy_threshold:
            return FactClaim(
                claim=claim,
                status=FactStatus.SUPPORTED,
                confidence=best_score,
                matched_source=best_match,
                evidence=[best_match],
            )
        elif best_score >= 0.4:
            return FactClaim(
                claim=claim,
                status=FactStatus.PARTIALLY_SUPPORTED,
                confidence=best_score,
                matched_source=best_match,
                evidence=[best_match],
            )
        else:
            return FactClaim(
                claim=claim,
                status=FactStatus.UNVERIFIED,
                confidence=best_score,
                matched_source=best_match,
            )

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Token-overlap similarity."""
        a_tokens = set(re.findall(r"\w+", a.lower()))
        b_tokens = set(re.findall(r"\w+", b.lower()))
        if not a_tokens or not b_tokens:
            return 0.0
        intersection = a_tokens & b_tokens
        union = a_tokens | b_tokens
        return len(intersection) / len(union) if union else 0.0
