"""
aegis.corpus.labelled.inventory
===============================
Builds and maintains the labelled dataset inventory with ground-truth mappings.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .task_mapping import CapabilityTask, TaskDatasetMapping


class LabelledDatasetRecord(BaseModel):
    dataset_id: str
    name: str
    source_id: str
    version: str
    primary_tasks: List[CapabilityTask]
    document_count: int
    annotation_format: str
    licence_id: str
    status: str
    sample_annotations_path: Optional[str] = None


class LabelledDatasetInventory:
    """Manages the catalog of ground-truth labelled datasets."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.datasets: Dict[str, LabelledDatasetRecord] = {}

    def build_default_inventory(self) -> List[LabelledDatasetRecord]:
        """Constructs canonical inventory from repository public corpus baseline."""
        self.datasets = {
            "DS-DOCLAYNET-01": LabelledDatasetRecord(
                dataset_id="DS-DOCLAYNET-01",
                name="DocLayNet Document Layout Benchmark",
                source_id="SRC-DOCLAYNET-001",
                version="1.1",
                primary_tasks=[CapabilityTask.LAYOUT_DETECTION],
                document_count=40,
                annotation_format="coco_json",
                licence_id="LIC-CDLA-PERMISSIVE-001",
                status="APPROVED",
                sample_annotations_path="audit/corpus/ground-truth/layout_ground_truth_sample.json",
            ),
            "DS-PUBTABNET-01": LabelledDatasetRecord(
                dataset_id="DS-PUBTABNET-01",
                name="PubTabNet Table Reconstruction Benchmark",
                source_id="SRC-PUBTABNET-001",
                version="1.0",
                primary_tasks=[CapabilityTask.TABLE_EXTRACTION],
                document_count=15,
                annotation_format="html_table_json",
                licence_id="LIC-CDLA-PERMISSIVE-001",
                status="APPROVED",
                sample_annotations_path="audit/corpus/ground-truth/table_ground_truth_sample.json",
            ),
            "DS-FUNSD-01": LabelledDatasetRecord(
                dataset_id="DS-FUNSD-01",
                name="FUNSD Form Entity & Key-Value Benchmark",
                source_id="SRC-FUNSD-001",
                version="1.0",
                primary_tasks=[CapabilityTask.ENTITY_EXTRACTION, CapabilityTask.OCR_EVALUATION],
                document_count=15,
                annotation_format="funsd_spatial_json",
                licence_id="LIC-FUNSD-ACAD-001",
                status="CONDITIONAL",
            ),
            "DS-DOCVQA-01": LabelledDatasetRecord(
                dataset_id="DS-DOCVQA-01",
                name="DocVQA Document Question Answering Benchmark",
                source_id="SRC-DOCVQA-001",
                version="1.0",
                primary_tasks=[CapabilityTask.QUESTION_ANSWERING, CapabilityTask.CITATION_VALIDATION],
                document_count=15,
                annotation_format="qa_evidence_json",
                licence_id="LIC-DOCVQA-CHALLENGE-001",
                status="CONDITIONAL",
            ),
            "DS-AEGIS-INTEL-01": LabelledDatasetRecord(
                dataset_id="DS-AEGIS-INTEL-01",
                name="AEGIS Document Intelligence Grounding & Conflict Benchmark",
                source_id="SRC-AEGIS-ADV-001",
                version="1.0",
                primary_tasks=[CapabilityTask.CITATION_VALIDATION, CapabilityTask.CROSS_DOCUMENT_ANALYSIS],
                document_count=10,
                annotation_format="jsonl",
                licence_id="LIC-APACHE-2-001",
                status="APPROVED",
                sample_annotations_path="evaluation/datasets/document_intelligence/extraction_cases.jsonl",
            ),
        }
        return list(self.datasets.values())

    def export_inventory(self, output_path: Path | str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        items = [d.model_dump() for d in self.datasets.values()]
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"catalog_version": "1.0.0", "datasets": items}, f, indent=2)
