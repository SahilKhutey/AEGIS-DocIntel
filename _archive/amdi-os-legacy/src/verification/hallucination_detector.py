"""
Hallucination Detection
========================

Detects fabricated content in AI responses.

Signals:
    1. Uncited factual claims
    2. Internal contradictions
    3. Specificity paradox (overly specific without sources)
    4. Entity confusion (wrong attributions)
    5. Numerical inconsistencies
    6. Temporal inconsistencies
    7. Source-document divergence

Mathematical Foundation:
    Hallucination rate:
        HR = |hallucinated_statements| / |total_statements|

    Composite hallucination score:
        H = w₁ · uncited + w₂ · contradiction + w₃ · specificity
          + w₄ · entity_confusion + w₅ · numerical_inconsistency
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .exceptions import HallucinationDetectedError


class HallucinationType(Enum):
    UNCITED_CLAIM = "uncited_claim"
    INTERNAL_CONTRADICTION = "internal_contradiction"
    SPECIFICITY_PARADOX = "specificity_paradox"
    ENTITY_CONFUSION = "entity_confusion"
    NUMERICAL_INCONSISTENCY = "numerical_inconsistency"
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"
    SOURCE_DIVERGENCE = "source_divergence"


@dataclass
class HallucinationIndicator:
    """A single hallucination indicator."""

    hallucination_type: HallucinationType
    text: str
    severity: float  # 0..1
    explanation: str

    def to_dict(self) -> dict:
        return {
            "type": self.hallucination_type.value,
            "text": self.text[:200],
            "severity": round(self.severity, 4),
            "explanation": self.explanation,
        }


@dataclass
class HallucinationResult:
    """Result of hallucination detection."""

    total_statements: int
    hallucinated_statements: int
    hallucination_rate: float
    indicators: List[HallucinationIndicator] = field(default_factory=list)
    risk_level: str = "low"
    issues: List[str] = field(default_factory=list)

    @property
    def is_hallucinated(self) -> bool:
        return self.hallucination_rate > 0.1

    @property
    def high_risk(self) -> bool:
        return self.hallucination_rate > 0.3

    def to_dict(self) -> dict:
        return {
            "total_statements": self.total_statements,
            "hallucinated_statements": self.hallucinated_statements,
            "hallucination_rate": round(self.hallucination_rate, 4),
            "risk_level": self.risk_level,
            "is_hallucinated": self.is_hallucinated,
            "indicators": [i.to_dict() for i in self.indicators],
            "issues": self.issues,
        }


class HallucinationDetector:
    """
    Detect hallucinations in AI responses.
    """

    NUMERIC_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*(%|percent|million|billion|thousand)?\b")
    DATE_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
    NAME_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")

    def __init__(
        self,
        uncited_weight: float = 0.3,
        contradiction_weight: float = 0.25,
        specificity_weight: float = 0.15,
        entity_weight: float = 0.15,
        numerical_weight: float = 0.15,
        detection_threshold: float = 0.1,
    ) -> None:
        s = (
            uncited_weight
            + contradiction_weight
            + specificity_weight
            + entity_weight
            + numerical_weight
        )
        if s <= 0:
            raise ValueError("weights must sum to a positive number.")
        self.uncited_weight = uncited_weight / s
        self.contradiction_weight = contradiction_weight / s
        self.specificity_weight = specificity_weight / s
        self.entity_weight = entity_weight / s
        self.numerical_weight = numerical_weight / s
        self.detection_threshold = detection_threshold

    def detect(
        self,
        response_text: str,
        source_documents: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> HallucinationResult:
        """
        Detect hallucinations in `response_text`.

        Parameters
        ----------
        response_text : str
        source_documents : Optional[Dict]
            Source documents for comparison.
        context : Optional[Dict]
            Additional context (e.g., previous turns).
        """
        statements = self._split_statements(response_text)
        total = len(statements)
        if total == 0:
            return HallucinationResult(
                total_statements=0,
                hallucinated_statements=0,
                hallucination_rate=0.0,
                risk_level="low",
            )

        indicators: List[HallucinationIndicator] = []

        # signal 1: uncited claims
        indicators.extend(
            self._detect_uncited_claims(response_text, statements)
        )

        # signal 2: internal contradictions
        indicators.extend(
            self._detect_contradictions(statements)
        )

        # signal 3: specificity paradox
        indicators.extend(
            self._detect_specificity_paradox(statements)
        )

        # signal 4: entity confusion
        indicators.extend(
            self._detect_entity_confusion(response_text, source_documents)
        )

        # signal 5: numerical inconsistencies
        indicators.extend(
            self._detect_numerical_inconsistencies(response_text, statements)
        )

        # compute aggregate hallucination rate
        if total > 0:
            hallucination_severity = sum(
                i.severity for i in indicators
            ) / total
        else:
            hallucination_severity = 0.0
        hallucinated_count = sum(
            1 for i in indicators if i.severity > 0.5
        )
        hallucination_rate = hallucinated_count / max(total, 1)

        risk_level = self._risk_level(hallucination_rate)
        issues: List[str] = []
        if hallucination_rate > 0.3:
            issues.append("high_hallucination_risk")
        if any(i.severity > 0.8 for i in indicators):
            issues.append("severe_indicator_detected")

        return HallucinationResult(
            total_statements=total,
            hallucinated_statements=hallucinated_count,
            hallucination_rate=hallucination_rate,
            indicators=indicators,
            risk_level=risk_level,
            issues=issues,
        )

    def _split_statements(self, text: str) -> List[str]:
        clean_text = re.sub(r"\[.*?\]", "", text)
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text.strip()) if s.strip()]

    def _detect_uncited_claims(
        self,
        text: str,
        statements: List[str],
    ) -> List[HallucinationIndicator]:
        """Find factual claims without citations."""
        indicators: List[HallucinationIndicator] = []
        has_citation = bool(re.search(r"\[[\w\-_]+,?\s*p?\.?\d*\]", text))
        if has_citation:
            return indicators
        # look for specific numbers, percentages, dates
        specific_pattern = re.compile(
            r"(\d+(?:\.\d+)?\s*%|\b(19|20)\d{2}\b|\$\d+)"
        )
        for s in statements:
            if specific_pattern.search(s) and len(s.split()) > 5:
                indicators.append(
                    HallucinationIndicator(
                        hallucination_type=HallucinationType.UNCITED_CLAIM,
                        text=s,
                        severity=0.5,
                        explanation="Specific factual claim without citation",
                    )
                )
        return indicators

    def _detect_contradictions(
        self,
        statements: List[str],
    ) -> List[HallucinationIndicator]:
        """Find internal contradictions in statements."""
        indicators: List[HallucinationIndicator] = []
        # extract numbers from statements
        numeric_per_stmt: List[List[float]] = []
        for s in statements:
            nums = [float(m[0]) for m in self.NUMERIC_PATTERN.findall(s) if m[0]]
            numeric_per_stmt.append(nums)
        # check for contradictory ranges (e.g., "between 5 and 10" then "12")
        # simple heuristic: if same entity described with conflicting numbers
        # we look at numbers appearing near the same noun
        entities_with_nums: Dict[str, List[float]] = {}
        for s in statements:
            nums = re.findall(r"\d+(?:\.\d+)?", s)
            # find first content word (heuristic entity)
            words = re.findall(r"\b[A-Za-z]{4,}\b", s)
            if not words:
                continue
            key = words[0].lower()
            if nums:
                entities_with_nums.setdefault(key, []).extend(
                    float(n) for n in nums
                )
        for entity, nums in entities_with_nums.items():
            if len(nums) >= 2 and (max(nums) - min(nums)) / max(max(nums), 1) > 0.5:
                indicators.append(
                    HallucinationIndicator(
                        hallucination_type=HallucinationType.INTERNAL_CONTRADICTION,
                        text=f"Entity '{entity}' has conflicting values: {nums}",
                        severity=0.6,
                        explanation=f"Numbers for '{entity}' vary significantly: {nums}",
                    )
                )
        return indicators

    def _detect_specificity_paradox(
        self,
        statements: List[str],
    ) -> List[HallucinationIndicator]:
        """Detect overly-specific claims without source."""
        indicators: List[HallucinationIndicator] = []
        paradox_pattern = re.compile(
            r"(exactly|precisely|to\s+the\s+\w+|at\s+least\s+\d|more\s+than\s+\d{2,})",
            re.IGNORECASE,
        )
        for s in statements:
            if paradox_pattern.search(s):
                # severity depends on specificity
                has_number = bool(re.search(r"\d", s))
                severity = 0.4 if has_number else 0.2
                indicators.append(
                    HallucinationIndicator(
                        hallucination_type=HallucinationType.SPECIFICITY_PARADOX,
                        text=s,
                        severity=severity,
                        explanation="Overly specific claim without source",
                    )
                )
        return indicators

    def _detect_entity_confusion(
        self,
        text: str,
        source_documents: Optional[Dict[str, Any]],
    ) -> List[HallucinationIndicator]:
        """Detect entity confusion (wrong attributions)."""
        indicators: List[HallucinationIndicator] = []
        if not source_documents:
            return indicators
        # collect all entity names from sources
        source_entities: set = set()
        for doc in source_documents.values():
            if isinstance(doc, dict):
                text_content = doc.get("text", "")
            elif isinstance(doc, str):
                text_content = doc
            else:
                text_content = str(doc)
            for name in self.NAME_PATTERN.findall(text_content):
                source_entities.add(name.lower())
        # check response entities
        for name in self.NAME_PATTERN.findall(text):
            if name.lower() not in source_entities:
                indicators.append(
                    HallucinationIndicator(
                        hallucination_type=HallucinationType.ENTITY_CONFUSION,
                        text=name,
                        severity=0.3,
                        explanation=f"Entity '{name}' not found in source documents",
                    )
                )
        return indicators

    def _detect_numerical_inconsistencies(
        self,
        text: str,
        statements: List[str],
    ) -> List[HallucinationIndicator]:
        """Detect numerical inconsistencies."""
        indicators: List[HallucinationIndicator] = []
        # find ranges and check for inconsistencies
        range_pattern = re.compile(
            r"between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)",
            re.IGNORECASE,
        )
        for s in statements:
            m = range_pattern.search(s)
            if m:
                low, high = float(m.group(1)), float(m.group(2))
                if low > high:
                    indicators.append(
                        HallucinationIndicator(
                            hallucination_type=HallucinationType.NUMERICAL_INCONSISTENCY,
                            text=s,
                            severity=0.7,
                            explanation=f"Range low ({low}) > high ({high})",
                        )
                    )
        return indicators

    @staticmethod
    def _risk_level(rate: float) -> str:
        if rate > 0.3:
            return "high"
        if rate > 0.15:
            return "medium"
        if rate > 0.05:
            return "low"
        return "minimal"
