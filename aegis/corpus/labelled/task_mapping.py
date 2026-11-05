"""
aegis.corpus.labelled.task_mapping
==================================
Maps AEGIS intelligence and extraction capabilities to standardized tasks and label requirements.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Set
from pydantic import BaseModel


class CapabilityTask(str, Enum):
    DOCUMENT_CLASSIFICATION = "document_classification"
    OCR_EVALUATION = "ocr_evaluation"
    LAYOUT_DETECTION = "layout_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    TABLE_EXTRACTION = "table_extraction"
    QUESTION_ANSWERING = "question_answering"
    CITATION_VALIDATION = "citation_validation"
    DOCUMENT_RETRIEVAL = "document_retrieval"
    CROSS_DOCUMENT_ANALYSIS = "cross_document_analysis"


class TaskDefinition(BaseModel):
    task: CapabilityTask
    description: str
    required_label_fields: List[str]
    primary_datasets: List[str]
    metric_standard: str


TASK_REGISTRY: Dict[CapabilityTask, TaskDefinition] = {
    CapabilityTask.DOCUMENT_CLASSIFICATION: TaskDefinition(
        task=CapabilityTask.DOCUMENT_CLASSIFICATION,
        description="Whole-document taxonomic category classification",
        required_label_fields=["document_class", "confidence"],
        primary_datasets=["RVL-CDIP", "DocLayNet"],
        metric_standard="Macro_F1_and_Accuracy",
    ),
    CapabilityTask.OCR_EVALUATION: TaskDefinition(
        task=CapabilityTask.OCR_EVALUATION,
        description="Character and word-level recognition fidelity over noisy scans",
        required_label_fields=["text", "box"],
        primary_datasets=["FUNSD", "CORD"],
        metric_standard="CER_and_WER",
    ),
    CapabilityTask.LAYOUT_DETECTION: TaskDefinition(
        task=CapabilityTask.LAYOUT_DETECTION,
        description="Region classification, bounding boxes, and reading order",
        required_label_fields=["bbox", "category", "reading_order"],
        primary_datasets=["DocLayNet", "PubLayNet"],
        metric_standard="Kendall_Tau_and_mAP",
    ),
    CapabilityTask.TABLE_EXTRACTION: TaskDefinition(
        task=CapabilityTask.TABLE_EXTRACTION,
        description="Table row, column, and cell HTML reconstruction",
        required_label_fields=["cells", "rows", "cols", "html"],
        primary_datasets=["PubTabNet"],
        metric_standard="Cell_F1",
    ),
    CapabilityTask.ENTITY_EXTRACTION: TaskDefinition(
        task=CapabilityTask.ENTITY_EXTRACTION,
        description="Spatial key-value and entity recognition",
        required_label_fields=["entity_type", "value", "box"],
        primary_datasets=["FUNSD", "CORD"],
        metric_standard="Entity_F1",
    ),
    CapabilityTask.QUESTION_ANSWERING: TaskDefinition(
        task=CapabilityTask.QUESTION_ANSWERING,
        description="Evidence-grounded question answering over document images/text",
        required_label_fields=["question", "answers", "evidence_page"],
        primary_datasets=["DocVQA"],
        metric_standard="ANLS_and_Exact_Match",
    ),
    CapabilityTask.CITATION_VALIDATION: TaskDefinition(
        task=CapabilityTask.CITATION_VALIDATION,
        description="Multi-layer claim verification and source attribution",
        required_label_fields=["claim_id", "claim_text", "citations"],
        primary_datasets=["AEGIS-Grounding", "DocVQA"],
        metric_standard="Citation_Precision_and_Coverage",
    ),
    CapabilityTask.CROSS_DOCUMENT_ANALYSIS: TaskDefinition(
        task=CapabilityTask.CROSS_DOCUMENT_ANALYSIS,
        description="Cross-document fact comparison and conflict detection",
        required_label_fields=["left_doc", "right_doc", "comparisons", "conflicts"],
        primary_datasets=["SEC-EDGAR-Pairs", "AEGIS-Conflict"],
        metric_standard="Conflict_Recall",
    ),
    CapabilityTask.DOCUMENT_RETRIEVAL: TaskDefinition(
        task=CapabilityTask.DOCUMENT_RETRIEVAL,
        description="Multi-strategy rank fusion and abstention accuracy",
        required_label_fields=["query", "relevant_ids", "top_relevant_id"],
        primary_datasets=["AEGIS-Benchmark", "WorldBank-Corpus"],
        metric_standard="MRR_and_Recall@5",
    ),
}


class TaskDatasetMapping:
    """Helper to validate task suitability and label conformance."""

    @classmethod
    def get_task_definition(cls, task: CapabilityTask) -> TaskDefinition:
        return TASK_REGISTRY[task]

    @classmethod
    def validate_labels(cls, task: CapabilityTask, labels: Dict[str, Any]) -> List[str]:
        defn = cls.get_task_definition(task)
        missing = [f for f in defn.required_label_fields if f not in labels]
        return [f"Task '{task.value}' missing required field: {f}" for f in missing]
