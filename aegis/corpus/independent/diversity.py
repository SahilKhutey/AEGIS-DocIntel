"""
aegis.corpus.independent.diversity
==================================
Audits diversity across categories, providers, formats, and page counts.
"""

from __future__ import annotations

from collections import Counter
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel

from .inventory import DocumentRecord, IndependentDocumentInventory


class DiversityReport(BaseModel):
    total_documents: int
    category_distribution: Dict[str, int]
    publisher_distribution: Dict[str, int]
    format_distribution: Dict[str, int]
    total_estimated_pages: int
    mean_pages_per_doc: float
    categories_covered_count: int
    is_diverse: bool


class DiversityAuditor:
    """Evaluates multi-domain representation in independent public document corpus."""

    REQUIRED_DOMAINS = {
        "Layout-Detection",
        "Scientific-MultiColumn",
        "Complex-Tables",
        "Form-Understanding",
        "Document-QA",
        "Long-Form-Policy",
        "Financial-Statements",
        "Government-Bilingual",
        "Technical-Math",
        "Adversarial-Edge-Cases",
    }

    @classmethod
    def evaluate_diversity(cls, documents: List[DocumentRecord]) -> DiversityReport:
        if not documents:
            return DiversityReport(
                total_documents=0,
                category_distribution={},
                publisher_distribution={},
                format_distribution={},
                total_estimated_pages=0,
                mean_pages_per_doc=0.0,
                categories_covered_count=0,
                is_diverse=False,
            )

        cat_counts = Counter(d.category for d in documents)
        pub_counts = Counter(d.publisher for d in documents)
        fmt_counts = Counter(d.file_format for d in documents)
        tot_pages = sum(d.pages_estimate for d in documents)

        covered = set(cat_counts.keys())
        is_diverse = len(covered) >= 8 and len(pub_counts) >= 8

        return DiversityReport(
            total_documents=len(documents),
            category_distribution=dict(cat_counts),
            publisher_distribution=dict(pub_counts),
            format_distribution=dict(fmt_counts),
            total_estimated_pages=tot_pages,
            mean_pages_per_doc=round(tot_pages / max(1, len(documents)), 2),
            categories_covered_count=len(covered),
            is_diverse=is_diverse,
        )

    @classmethod
    def export_report(cls, documents: List[DocumentRecord], output_path: Path | str) -> Dict[str, Any]:
        rep = cls.evaluate_diversity(documents)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "report_version": "1.0.0",
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **rep.model_dump(),
        }
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data
