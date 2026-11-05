"""
aegis.intelligence.citations
============================
Citation and claim entailment evaluation modules:
ClaimExtractor, CitationResolver, SupportEvaluator, and citation benchmark runner.
"""

from aegis.intelligence.citations.benchmark import run_citation_benchmark
from aegis.intelligence.citations.citation_resolver import CitationResolver
from aegis.intelligence.citations.claim_extractor import ClaimExtractor
from aegis.intelligence.citations.support_evaluator import SupportEvaluator

__all__ = [
    "CitationResolver",
    "ClaimExtractor",
    "SupportEvaluator",
    "run_citation_benchmark",
]
