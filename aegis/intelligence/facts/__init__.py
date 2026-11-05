"""
aegis.intelligence.facts
========================
Canonical Fact extraction and evaluation modules.
"""

from aegis.intelligence.facts.benchmark import run_facts_and_conflicts_benchmark
from aegis.intelligence.facts.extractor import FactExtractor

__all__ = [
    "FactExtractor",
    "run_facts_and_conflicts_benchmark",
]
