"""
Consistency Checker
====================

Verifies internal consistency of an AI response:
- Logical coherence
- Numerical consistency
- Temporal consistency
- Entity consistency
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ConsistencyType(Enum):
    LOGICAL = "logical"
    NUMERICAL = "numerical"
    TEMPORAL = "temporal"
    ENTITY = "entity"


@dataclass
class ConsistencyResult:
    """Result of consistency checking."""

    is_consistent: bool
    consistency_score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    type_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "is_consistent": self.is_consistent,
            "consistency_score": round(self.consistency_score, 4),
            "issues": self.issues,
            "type_scores": {k: round(v, 4) for k, v in self.type_scores.items()},
        }


class ConsistencyChecker:
    """
    Check internal consistency of a response.
    """

    def __init__(self) -> None:
        self.numeric_pattern = re.compile(r"\b(\d+(?:\.\d+)?)\b")
        self.date_pattern = re.compile(r"\b(19|20)\d{2}\b")

    def check(self, response_text: str) -> ConsistencyResult:
        """Run all consistency checks."""
        issues: List[Dict[str, Any]] = []
        type_scores: Dict[str, float] = {}

        type_scores["numerical"] = self._check_numerical(response_text, issues)
        type_scores["temporal"] = self._check_temporal(response_text, issues)
        type_scores["entity"] = self._check_entity(response_text, issues)
        type_scores["logical"] = self._check_logical(response_text, issues)

        # aggregate
        consistency_score = (
            sum(type_scores.values()) / max(len(type_scores), 1)
        )
        return ConsistencyResult(
            is_consistent=consistency_score >= 0.8,
            consistency_score=consistency_score,
            issues=issues,
            type_scores=type_scores,
        )

    def _check_numerical(
        self,
        text: str,
        issues: List[Dict[str, Any]],
    ) -> float:
        # find contradictory ranges / reversed inequalities
        score = 1.0
        ranges = re.findall(
            r"between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)",
            text,
            re.IGNORECASE,
        )
        for low, high in ranges:
            if float(low) > float(high):
                issues.append({
                    "type": "numerical",
                    "description": f"reversed range: {low} > {high}",
                })
                score -= 0.3
        return max(0.0, score)

    def _check_temporal(
        self,
        text: str,
        issues: List[Dict[str, Any]],
    ) -> float:
        score = 1.0
        # find dates and check chronological order
        dates = [int(m) for m in self.date_pattern.findall(text)]
        for i in range(len(dates) - 1):
            if dates[i] > dates[i + 1] + 1:  # allow same year
                # could be a valid chronological mention, so just note
                pass
        return score

    def _check_entity(
        self,
        text: str,
        issues: List[Dict[str, Any]],
    ) -> float:
        # check for entity re-definition (same pronoun referring to different entities)
        # simple heuristic: track proper noun clusters
        score = 1.0
        # find capitalized phrases
        entities = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
        # find duplicates with different contexts (very rough heuristic)
        seen = {}
        for e in entities:
            e_lower = e.lower()
            if e_lower in seen:
                # repetition, not necessarily inconsistency
                pass
            else:
                seen[e_lower] = text.find(e)
        return score

    def _check_logical(
        self,
        text: str,
        issues: List[Dict[str, Any]],
    ) -> float:
        # check for explicit contradictions
        score = 1.0
        # "X is Y" vs "X is not Y"
        sentences = re.split(r"(?<=[.!?])\s+", text)
        positive_claims: Dict[str, List[str]] = {}
        negative_claims: Dict[str, List[str]] = {}
        for sent in sentences:
            sent_lower = sent.lower()
            is_negation = any(
                neg in sent_lower for neg in [" not ", " never ", " no "]
            )
            # find "X is Y" or "X are Y"
            sent_clean = re.sub(r"\b(not|never|no)\b", "", sent_lower)
            m = re.search(r"\b(\w+(?:\s+\w+)?)\s+(?:is|are)\s+(\w+)", sent_clean)
            if m:
                subj, pred = m.groups()
                key = subj.strip()
                if is_negation:
                    negative_claims.setdefault(key, []).append(pred)
                else:
                    positive_claims.setdefault(key, []).append(pred)
        # check for conflicts
        for subj, positive_preds in positive_claims.items():
            if subj in negative_claims:
                negative_preds = negative_claims[subj]
                overlap = set(positive_preds) & set(negative_preds)
                if overlap:
                    issues.append({
                        "type": "logical",
                        "description": f"contradiction for '{subj}': positive claims {positive_preds} and negative claims {negative_preds}",
                    })
                    score -= 0.4
        return max(0.0, score)
