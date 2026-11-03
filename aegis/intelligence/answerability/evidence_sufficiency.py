"""
aegis.intelligence.answerability.evidence_sufficiency
=====================================================
Multi-signal evidence sufficiency evaluation.
Computes a calibrated score [0.0, 1.0] representing whether retrieved evidence
is sufficient to answer the question without hallucination.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from aegis.intelligence.models import AnswerabilitySignals, RetrievalItem


class EvidenceSufficiencyScorer:
    """Computes a multi-signal evidence sufficiency score."""

    def __init__(
        self,
        min_relevance_threshold: float = 0.30,
        min_chunks_required: int = 1,
    ):
        self.min_relevance_threshold = min_relevance_threshold
        self.min_chunks_required = min_chunks_required

    @staticmethod
    def _extract_question_keywords(question: str) -> Set[str]:
        words = re.findall(r"\b[A-Za-z0-9_\-\$]+\b", question.lower())
        stopwords = {
            "what", "who", "where", "when", "why", "how", "is", "was", "are",
            "were", "did", "does", "the", "a", "an", "in", "on", "of", "to",
            "for", "and", "or", "which",
        }
        return {w for w in words if w not in stopwords and len(w) > 1}

    def compute_sufficiency(
        self,
        question: str,
        retrieved_items: List[RetrievalItem],
        contradiction_detected: bool = False,
        policy_restricted: bool = False,
    ) -> tuple[float, AnswerabilitySignals]:
        """Compute sufficiency score [0.0, 1.0] and return extracted signal telemetry."""
        q_keywords = self._extract_question_keywords(question)
        chunk_count = len(retrieved_items)
        max_rel = max([item.score for item in retrieved_items], default=0.0)
        sources = {item.document_id for item in retrieved_items}

        if policy_restricted:
            signals = AnswerabilitySignals(
                retrieved_chunk_count=chunk_count,
                max_relevance_score=max_rel,
                source_count=len(sources),
                contradiction_detected=contradiction_detected,
                missing_required_fields=["RESTRICTED_ACCESS_POLICY"],
            )
            return 0.0, signals

        if chunk_count == 0 or max_rel < self.min_relevance_threshold:
            signals = AnswerabilitySignals(
                retrieved_chunk_count=chunk_count,
                max_relevance_score=max_rel,
                source_count=len(sources),
                contradiction_detected=contradiction_detected,
                missing_required_fields=list(q_keywords),
            )
            return 0.0, signals

        # Assess keyword grounding in retrieved text
        combined_text = " ".join([item.text.lower() for item in retrieved_items])
        grounded_keywords = {w for w in q_keywords if w in combined_text}
        missing_keywords = q_keywords - grounded_keywords

        coverage_ratio = len(grounded_keywords) / max(1, len(q_keywords))

        # Base score components
        # 1. Relevance score component (up to 0.40)
        s_rel = min(0.40, max_rel * 0.40)
        # 2. Keyword coverage component (up to 0.40)
        s_cov = coverage_ratio * 0.40
        # 3. Source corroboration component (up to 0.20)
        s_src = min(0.20, len(sources) * 0.10)

        raw_score = s_rel + s_cov + s_src

        # Penalties
        if contradiction_detected:
            raw_score *= 0.50
        if coverage_ratio < 0.50:
            raw_score *= 0.60

        final_score = round(min(1.0, max(0.0, raw_score)), 4)

        signals = AnswerabilitySignals(
            retrieved_chunk_count=chunk_count,
            max_relevance_score=round(max_rel, 4),
            source_count=len(sources),
            contradiction_detected=contradiction_detected,
            missing_required_fields=sorted(list(missing_keywords)),
        )

        return final_score, signals
