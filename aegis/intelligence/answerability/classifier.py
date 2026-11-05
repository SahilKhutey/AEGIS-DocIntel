"""
aegis.intelligence.answerability.classifier
===========================================
Classifies questions into canonical answerability categories:
ANSWERABLE, NOT_FOUND, INSUFFICIENT_EVIDENCE, AMBIGUOUS, CONFLICTING_EVIDENCE, OUT_OF_SCOPE, RESTRICTED.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from aegis.intelligence.answerability.evidence_sufficiency import EvidenceSufficiencyScorer
from aegis.intelligence.models import (
    AnswerabilityClass,
    AnswerabilityDecision,
    AnswerabilityResult,
    AnswerabilitySignals,
    RetrievalItem,
)


class AnswerabilityClassifier:
    """Multi-stage answerability and abstention decision engine."""

    RESTRICTED_KEYWORDS = {"password", "secret", "private key", "covert", "classified", "pin code", "credential"}
    OUT_OF_SCOPE_PATTERNS = [r"\bin 20[3-9]\d\b", r"\balien\b", r"\bextraterrestrial\b", r"\bfuture\b"]
    AMBIGUOUS_PATTERNS = [r"^what was the total\??$", r"^what was the revenue\??$", r"^what was the headcount\??$", r"^what was the budget\??$"]

    def __init__(
        self,
        sufficiency_scorer: Optional[EvidenceSufficiencyScorer] = None,
        answer_threshold: float = 0.50,
        partial_threshold: float = 0.30,
    ):
        self.scorer = sufficiency_scorer or EvidenceSufficiencyScorer()
        self.answer_threshold = answer_threshold
        self.partial_threshold = partial_threshold

    def evaluate(
        self,
        question_id: str,
        question: str,
        retrieved_items: List[RetrievalItem],
        contradiction_detected: bool = False,
        policy_restricted: bool = False,
    ) -> AnswerabilityResult:
        """Classify question and determine whether to answer, clarify, disclose conflict, or abstain."""
        q_lower = question.lower().strip()

        # 1. Check for Restricted Information Policy
        if policy_restricted or any(k in q_lower for k in self.RESTRICTED_KEYWORDS):
            _, signals = self.scorer.compute_sufficiency(question, retrieved_items, policy_restricted=True)
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.RESTRICTED,
                evidence_sufficiency_score=0.0,
                decision=AnswerabilityDecision.DENY_RESTRICTED,
                signals=signals,
                explanation="Requested information falls under security/privacy restricted access policies.",
            )

        # 2. Check for Out-of-Scope / Speculative Inquiries
        if any(re.search(p, q_lower) for p in self.OUT_OF_SCOPE_PATTERNS):
            _, signals = self.scorer.compute_sufficiency(question, retrieved_items)
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.OUT_OF_SCOPE,
                evidence_sufficiency_score=0.0,
                decision=AnswerabilityDecision.ABSTAIN_NOT_FOUND,
                signals=signals,
                explanation="Question references future or out-of-scope domain subjects beyond verified corpus.",
            )

        # 3. Check for Ambiguity / Under-specified Questions
        if any(re.search(p, q_lower) for p in self.AMBIGUOUS_PATTERNS) or len(question.split()) < 4:
            _, signals = self.scorer.compute_sufficiency(question, retrieved_items)
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.AMBIGUOUS,
                evidence_sufficiency_score=0.20,
                decision=AnswerabilityDecision.REQUEST_CLARIFICATION,
                signals=signals,
                explanation="Question is ambiguous and requires scope/category clarification.",
            )

        # 4. Check for Conflicting Evidence
        if contradiction_detected:
            score, signals = self.scorer.compute_sufficiency(
                question, retrieved_items, contradiction_detected=True
            )
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.CONFLICTING_EVIDENCE,
                evidence_sufficiency_score=score,
                decision=AnswerabilityDecision.DISCLOSE_CONFLICT,
                signals=signals,
                explanation="Retrieved sources contain contradictory assertions on the subject.",
            )

        # 5. Evaluate Multi-Signal Sufficiency Score
        score, signals = self.scorer.compute_sufficiency(
            question, retrieved_items, contradiction_detected=False
        )

        if score >= self.answer_threshold:
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.ANSWERABLE,
                evidence_sufficiency_score=score,
                decision=AnswerabilityDecision.ANSWER,
                signals=signals,
                explanation="Sufficient relevant evidence retrieved with high keyword grounding.",
            )
        elif score >= self.partial_threshold:
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.INSUFFICIENT_EVIDENCE,
                evidence_sufficiency_score=score,
                decision=AnswerabilityDecision.ABSTAIN_INSUFFICIENT,
                signals=signals,
                explanation="Some evidence was retrieved, but critical factual components are missing.",
            )
        else:
            return AnswerabilityResult(
                question_id=question_id,
                classification=AnswerabilityClass.NOT_FOUND,
                evidence_sufficiency_score=score,
                decision=AnswerabilityDecision.ABSTAIN_NOT_FOUND,
                signals=signals,
                explanation="No relevant evidence exists in the indexed document corpus.",
            )
