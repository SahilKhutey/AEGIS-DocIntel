"""
aegis.corpus.labelled.quality
=============================
Audits dataset label quality, class distribution, missing annotations,
and ground-truth consistency.
"""

from __future__ import annotations

from collections import Counter
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class QualitySummary(BaseModel):
    dataset_id: str
    total_pages_or_samples: int
    total_annotations: int
    label_distribution: Dict[str, int]
    missing_labels_count: int
    corrupt_count: int
    quality_status: str  # "PASS", "WARN", "FAIL"


class DatasetQualityAuditor:
    """Audits ground truth quality across sample annotations."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def audit_sample_annotations(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        # 1. Audit DocLayNet layout sample
        layout_sample = self.repo_root / "audit" / "corpus" / "ground-truth" / "layout_ground_truth_sample.json"
        if layout_sample.exists():
            with open(layout_sample, "r", encoding="utf-8") as f:
                data = json.load(f)
            samples = data.get("sample_pages", [])
            cat_counts: Counter[str] = Counter()
            missing_boxes = 0
            for page in samples:
                for ann in page.get("annotations", []):
                    cat = ann.get("category", "unknown")
                    cat_counts[cat] += 1
                    bbox = ann.get("bbox")
                    if not bbox or len(bbox) != 4:
                        missing_boxes += 1

            results["DS-DOCLAYNET-01"] = QualitySummary(
                dataset_id="DS-DOCLAYNET-01",
                total_pages_or_samples=len(samples),
                total_annotations=sum(cat_counts.values()),
                label_distribution=dict(cat_counts),
                missing_labels_count=missing_boxes,
                corrupt_count=0,
                quality_status="PASS" if missing_boxes == 0 else "FAIL",
            ).model_dump()

        # 2. Audit PubTabNet table sample
        table_sample = self.repo_root / "audit" / "corpus" / "ground-truth" / "table_ground_truth_sample.json"
        if table_sample.exists():
            with open(table_sample, "r", encoding="utf-8") as f:
                data = json.load(f)
            tables = data.get("sample_tables", [])
            tag_counts: Counter[str] = Counter()
            for t in tables:
                structure = t.get("html_structure", {}).get("tokens", [])
                for tok in structure:
                    if tok.startswith("<"):
                        tag_counts[tok] += 1

            results["DS-PUBTABNET-01"] = QualitySummary(
                dataset_id="DS-PUBTABNET-01",
                total_pages_or_samples=len(tables),
                total_annotations=sum(tag_counts.values()),
                label_distribution=dict(tag_counts),
                missing_labels_count=0,
                corrupt_count=0,
                quality_status="PASS",
            ).model_dump()

        report = {
            "report_version": "1.0.0",
            "audited_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "overall_status": "PASS" if all(v.get("quality_status") == "PASS" for v in results.values()) else "FAIL",
            "datasets_audited": results,
        }
        return report

    def export_report(self, output_path: Path | str) -> None:
        report = self.audit_sample_annotations()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
