"""
tests/corpus/test_labelled_datasets.py
======================================
Tests verifying task-to-dataset mapping, ground truth annotations,
label schema validation, and quality auditing.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.corpus.labelled.task_mapping import CapabilityTask, TaskDatasetMapping
from aegis.corpus.labelled.inventory import LabelledDatasetInventory
from aegis.corpus.labelled.quality import DatasetQualityAuditor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_lab_001_task_mapping_coverage():
    """LAB-001: All core intelligence capabilities have task definitions and label requirements."""
    for task in CapabilityTask:
        defn = TaskDatasetMapping.get_task_definition(task)
        assert defn is not None
        assert len(defn.required_label_fields) > 0
        assert len(defn.primary_datasets) > 0


def test_lab_002_label_validation_success():
    """LAB-002: Valid layout detection labels pass validation."""
    valid_labels = {"bbox": [0, 0, 100, 100], "category": "Title", "reading_order": 1}
    errors = TaskDatasetMapping.validate_labels(CapabilityTask.LAYOUT_DETECTION, valid_labels)
    assert len(errors) == 0


def test_lab_003_label_validation_missing_field():
    """LAB-003: Label validation detects missing required fields."""
    incomplete_labels = {"bbox": [0, 0, 100, 100]}  # missing category and reading_order
    errors = TaskDatasetMapping.validate_labels(CapabilityTask.LAYOUT_DETECTION, incomplete_labels)
    assert len(errors) == 2


def test_lab_004_inventory_construction():
    """LAB-004: LabelledDatasetInventory creates catalog covering multi-domain tasks."""
    inventory = LabelledDatasetInventory(REPO_ROOT)
    datasets = inventory.build_default_inventory()
    assert len(datasets) >= 5
    assert any(d.dataset_id == "DS-DOCLAYNET-01" for d in datasets)
    assert any(d.dataset_id == "DS-PUBTABNET-01" for d in datasets)
    assert any(d.dataset_id == "DS-FUNSD-01" for d in datasets)


def test_lab_005_quality_auditor_sample_eval():
    """LAB-005: DatasetQualityAuditor analyzes DocLayNet and PubTabNet samples."""
    auditor = DatasetQualityAuditor(REPO_ROOT)
    report = auditor.audit_sample_annotations()
    assert report["overall_status"] == "PASS"
    assert "DS-DOCLAYNET-01" in report["datasets_audited"]
    assert "DS-PUBTABNET-01" in report["datasets_audited"]
    doclay = report["datasets_audited"]["DS-DOCLAYNET-01"]
    assert doclay["total_annotations"] > 0
    assert doclay["missing_labels_count"] == 0
