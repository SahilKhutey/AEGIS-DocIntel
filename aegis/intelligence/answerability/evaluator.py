"""
aegis.intelligence.answerability.evaluator
=========================================
Computes abstention metrics: Abstention Precision, Abstention Recall,
Answer Coverage, Selective Risk, and Unsupported Answer Rate.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from aegis.intelligence.models import (
    AnswerabilityClass,
    AnswerabilityDecision,
    AnswerabilityResult,
)


class AbstentionMetrics(BaseModel):
    total_questions: int
    unanswerable_questions_count: int
    answerable_questions_count: int
    abstention_precision: float = Field(ge=0.0, le=1.0)
    abstention_recall: float = Field(ge=0.0, le=1.0)
    answer_coverage: float = Field(ge=0.0, le=1.0)
    selective_risk: float = Field(ge=0.0, le=1.0)
    unsupported_answer_rate: float = Field(ge=0.0, le=1.0)


class AbstentionEvaluator:
    """Evaluates answerability decisions against ground truth expected classes."""

    @classmethod
    def evaluate_batch(
        cls,
        eval_cases: List[Dict[str, Any]],
    ) -> AbstentionMetrics:
        """
        eval_cases structure:
        [
            {
                "result": AnswerabilityResult,
                "expected_answerability": AnswerabilityClass,
                "expected_decision": AnswerabilityDecision (optional),
                "is_answer_correct": bool (optional, for selective risk)
            },
            ...
        ]
        """
        total = len(eval_cases)
        if total == 0:
            return AbstentionMetrics(
                total_questions=0,
                unanswerable_questions_count=0,
                answerable_questions_count=0,
                abstention_precision=1.0,
                abstention_recall=1.0,
                answer_coverage=0.0,
                selective_risk=0.0,
                unsupported_answer_rate=0.0,
            )

        unanswerable_classes = {
            AnswerabilityClass.NOT_FOUND,
            AnswerabilityClass.INSUFFICIENT_EVIDENCE,
            AnswerabilityClass.AMBIGUOUS,
            AnswerabilityClass.CONFLICTING_EVIDENCE,
            AnswerabilityClass.OUT_OF_SCOPE,
            AnswerabilityClass.RESTRICTED,
        }

        abstention_decisions = {
            AnswerabilityDecision.ABSTAIN_NOT_FOUND,
            AnswerabilityDecision.ABSTAIN_INSUFFICIENT,
            AnswerabilityDecision.REQUEST_CLARIFICATION,
            AnswerabilityDecision.DISCLOSE_CONFLICT,
            AnswerabilityDecision.DENY_RESTRICTED,
        }

        total_unanswerable = 0
        total_answerable = 0
        all_abstained = 0
        correct_abstained = 0
        total_answered = 0
        incorrect_answered = 0
        unsupported_answered = 0

        for case in eval_cases:
            res: AnswerabilityResult = case["result"]
            exp_ans: AnswerabilityClass = case["expected_answerability"]
            is_correct: bool = case.get("is_answer_correct", True)

            is_exp_unans = exp_ans in unanswerable_classes
            if is_exp_unans:
                total_unanswerable += 1
            else:
                total_answerable += 1

            did_abstain = res.decision in abstention_decisions
            if did_abstain:
                all_abstained += 1
                if is_exp_unans:
                    correct_abstained += 1
            else:
                total_answered += 1
                if is_exp_unans:
                    unsupported_answered += 1
                    incorrect_answered += 1
                elif not is_correct:
                    incorrect_answered += 1

        abs_prec = (correct_abstained / all_abstained) if all_abstained > 0 else 1.0
        abs_rec = (correct_abstained / total_unanswerable) if total_unanswerable > 0 else 1.0
        ans_cov = (total_answered / total) if total > 0 else 0.0
        sel_risk = (incorrect_answered / total_answered) if total_answered > 0 else 0.0
        unsupp_rate = (unsupported_answered / total) if total > 0 else 0.0

        return AbstentionMetrics(
            total_questions=total,
            unanswerable_questions_count=total_unanswerable,
            answerable_questions_count=total_answerable,
            abstention_precision=round(abs_prec, 4),
            abstention_recall=round(abs_rec, 4),
            answer_coverage=round(ans_cov, 4),
            selective_risk=round(sel_risk, 4),
            unsupported_answer_rate=round(unsupp_rate, 4),
        )
