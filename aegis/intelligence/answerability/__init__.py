"""
aegis.intelligence.answerability
================================
Answerability classification, evidence sufficiency scoring, and abstention benchmarking.
"""

from aegis.intelligence.answerability.benchmark import run_abstention_benchmark
from aegis.intelligence.answerability.classifier import AnswerabilityClassifier
from aegis.intelligence.answerability.evaluator import (
    AbstentionEvaluator,
    AbstentionMetrics,
)
from aegis.intelligence.answerability.evidence_sufficiency import (
    EvidenceSufficiencyScorer,
)

__all__ = [
    "AbstentionEvaluator",
    "AbstentionMetrics",
    "AnswerabilityClassifier",
    "EvidenceSufficiencyScorer",
    "run_abstention_benchmark",
]
