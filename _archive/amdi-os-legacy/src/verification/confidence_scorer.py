"""
Confidence Scoring
==================

Aggregate confidence from multiple verification signals.

Mathematical Foundation:
    Composite confidence:
        C = w_c · CA
          + w_f · FA
          + w_h · (1 - HR)
          + w_e · EV
          + w_s · SR

where:
    CA  citation accuracy
    FA  fact accuracy
    HR  hallucination rate
    EV  explained variance (from decomposition)
    SR  source reliability
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import ConfidenceThresholdError


@dataclass
class ConfidenceScore:
    """Composite confidence score."""

    overall: float
    citation_confidence: float
    fact_confidence: float
    hallucination_penalty: float
    source_reliability: float
    explained_variance: float
    components: Dict[str, float] = field(default_factory=dict)
    grade: str = "unknown"
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "overall": round(self.overall, 4),
            "grade": self.grade,
            "citation_confidence": round(self.citation_confidence, 4),
            "fact_confidence": round(self.fact_confidence, 4),
            "hallucination_penalty": round(self.hallucination_penalty, 4),
            "source_reliability": round(self.source_reliability, 4),
            "explained_variance": round(self.explained_variance, 4),
            "components": {k: round(v, 4) for k, v in self.components.items()},
            "issues": self.issues,
        }


class ConfidenceScorer:
    """
    Compute composite confidence from verification signals.
    """

    GRADES = [
        (0.9, "A"),
        (0.8, "B"),
        (0.7, "C"),
        (0.6, "D"),
        (0.0, "F"),
    ]

    def __init__(
        self,
        citation_weight: float = 0.3,
        fact_weight: float = 0.3,
        hallucination_weight: float = 0.2,
        source_weight: float = 0.1,
        explained_variance_weight: float = 0.1,
        passing_threshold: float = 0.7,
    ) -> None:
        s = (
            citation_weight
            + fact_weight
            + hallucination_weight
            + source_weight
            + explained_variance_weight
        )
        if s <= 0:
            raise ValueError("weights must sum to a positive number.")
        self.citation_weight = citation_weight / s
        self.fact_weight = fact_weight / s
        self.hallucination_weight = hallucination_weight / s
        self.source_weight = source_weight / s
        self.explained_variance_weight = explained_variance_weight / s
        self.passing_threshold = passing_threshold

    def score(
        self,
        citation_accuracy: float = 1.0,
        fact_accuracy: float = 1.0,
        hallucination_rate: float = 0.0,
        source_reliability: float = 1.0,
        explained_variance: float = 1.0,
        extra_components: Optional[Dict[str, float]] = None,
    ) -> ConfidenceScore:
        """
        Compute composite confidence.

        Parameters
        ----------
        citation_accuracy : float
            Citation accuracy in [0, 1].
        fact_accuracy : float
            Fact accuracy in [0, 1].
        hallucination_rate : float
            Hallucination rate in [0, 1].
        source_reliability : float
            Source reliability in [0, 1].
        explained_variance : float
            Decomposition explained variance in [0, 1].
        extra_components : Optional[Dict]
            Additional signals.
        """
        hallucination_penalty = max(0.0, 1.0 - hallucination_rate)
        components: Dict[str, float] = {
            "citation_accuracy": citation_accuracy,
            "fact_accuracy": fact_accuracy,
            "hallucination_penalty": hallucination_penalty,
            "source_reliability": source_reliability,
            "explained_variance": explained_variance,
        }
        if extra_components:
            components.update(extra_components)

        overall = (
            self.citation_weight * citation_accuracy
            + self.fact_weight * fact_accuracy
            + self.hallucination_weight * hallucination_penalty
            + self.source_weight * source_reliability
            + self.explained_variance_weight * explained_variance
        )
        # clamp
        overall = max(0.0, min(1.0, overall))
        grade = self._grade(overall)
        issues: List[str] = []
        if overall < self.passing_threshold:
            issues.append(
                f"below_threshold:{overall:.3f}<{self.passing_threshold}"
            )
        if hallucination_rate > 0.1:
            issues.append(f"high_hallucination:{hallucination_rate:.3f}")
        if citation_accuracy < 0.5:
            issues.append(f"low_citation_accuracy:{citation_accuracy:.3f}")
        if fact_accuracy < 0.5:
            issues.append(f"low_fact_accuracy:{fact_accuracy:.3f}")

        return ConfidenceScore(
            overall=overall,
            citation_confidence=citation_accuracy,
            fact_confidence=fact_accuracy,
            hallucination_penalty=hallucination_penalty,
            source_reliability=source_reliability,
            explained_variance=explained_variance,
            components=components,
            grade=grade,
            issues=issues,
        )

    def score_or_raise(self, **kwargs) -> ConfidenceScore:
        """Score and raise if below threshold."""
        score = self.score(**kwargs)
        if score.overall < self.passing_threshold:
            raise ConfidenceThresholdError(
                f"Confidence {score.overall:.3f} below threshold "
                f"{self.passing_threshold}."
            )
        return score

    def _grade(self, score: float) -> str:
        for threshold, letter in self.GRADES:
            if score >= threshold:
                return letter
        return "F"
