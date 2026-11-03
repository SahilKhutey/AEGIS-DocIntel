"""
aegis.corpus.adapters.custom_json
=================================
Adapter for AEGIS canonical JSON and JSONL datasets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from aegis.corpus.adapters.base import DatasetAdapter
from aegis.corpus.adapters.models import (
    BoundingBoxItem,
    CanonicalAnnotation,
    CanonicalDocument,
    CanonicalEvaluationItem,
    ContentInfo,
    EvidenceSpan,
    MetadataInfo,
    RightsInfo,
)


class CustomJSONAdapter(DatasetAdapter):
    """Adapter for AEGIS-native or custom formatted JSON and JSONL datasets."""

    @property
    def adapter_name(self) -> str:
        return "CustomJSON"

    @property
    def supported_formats(self) -> List[str]:
        return [".json", ".jsonl", "custom_json"]

    def validate_source(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if not p.is_file():
            return False
        if p.suffix.lower() not in [".json", ".jsonl"]:
            return False
        try:
            with open(p, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if not first_line:
                    return False
                if first_line.startswith("{") or first_line.startswith("["):
                    return True
        except Exception:
            return False
        return False

    def _read_records(self, path: Path) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if path.suffix.lower() == ".jsonl":
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                if "documents" in data:
                    records = data["documents"]
                elif "items" in data:
                    records = data["items"]
                else:
                    records = [data]
        return records

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        records = self._read_records(Path(path))
        dataset_id = kwargs.get("dataset_id", "CUSTOM").upper()

        for r in records:
            if "document_id" not in r:
                continue

            content_dict = r.get("content", {})
            metadata_dict = r.get("metadata", {})
            rights_dict = r.get("rights", {})

            yield CanonicalDocument(
                document_id=r["document_id"],
                source_id=r.get("source_id", "SRC-BENCHMARK-REAL"),
                dataset_id=r.get("dataset_id", dataset_id),
                content=ContentInfo(
                    uri=content_dict.get("uri", f"{r['document_id']}.pdf"),
                    format=content_dict.get("format", "application/pdf"),
                    sha256=content_dict.get("sha256", "0" * 64),
                    size_bytes=content_dict.get("size_bytes"),
                ),
                metadata=MetadataInfo(
                    title=metadata_dict.get("title", f"Document {r['document_id']}"),
                    document_type=metadata_dict.get("document_type", "report"),
                    language=metadata_dict.get("language", ["en"]),
                    page_count=metadata_dict.get("page_count", 1),
                    publication_date=metadata_dict.get("publication_date"),
                    publisher=metadata_dict.get("publisher"),
                ),
                rights=RightsInfo(
                    licence_id=rights_dict.get("licence_id", "LIC-CC-BY-4-001"),
                    status=rights_dict.get("status", "APPROVED"),
                    attribution_required=rights_dict.get("attribution_required", False),
                    attribution_text=rights_dict.get("attribution_text"),
                ),
            )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        records = self._read_records(Path(path))
        for r in records:
            if "annotation_id" in r:
                bboxes = [BoundingBoxItem(**b) for b in r.get("bounding_boxes", [])]
                spans = [EvidenceSpan(**s) for s in r.get("evidence_spans", [])]
                yield CanonicalAnnotation(
                    annotation_id=r["annotation_id"],
                    document_id=r["document_id"],
                    task=r.get("task", "document_classification"),
                    schema_version=r.get("schema_version", "1.0.0"),
                    labels=r.get("labels", {}),
                    bounding_boxes=bboxes,
                    evidence_spans=spans,
                )
            elif "annotations" in r and isinstance(r["annotations"], list):
                for ann in r["annotations"]:
                    bboxes = [BoundingBoxItem(**b) for b in ann.get("bounding_boxes", [])]
                    spans = [EvidenceSpan(**s) for s in ann.get("evidence_spans", [])]
                    yield CanonicalAnnotation(
                        annotation_id=ann.get("annotation_id", f"ANNO-{r.get('document_id', 'DOC')}"),
                        document_id=r.get("document_id", ann.get("document_id")),
                        task=ann.get("task", "document_classification"),
                        schema_version=ann.get("schema_version", "1.0.0"),
                        labels=ann.get("labels", {}),
                        bounding_boxes=bboxes,
                        evidence_spans=spans,
                    )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        records = self._read_records(Path(path))
        for r in records:
            if "item_id" in r:
                yield CanonicalEvaluationItem(
                    item_id=r["item_id"],
                    document_id=r["document_id"],
                    task=r.get("task", "citation_validation"),
                    input=r.get("input", {}),
                    ground_truth=r.get("ground_truth", {}),
                    evidence=r.get("evidence", []),
                    annotation_version=r.get("annotation_version", "1.0.0"),
                )
            elif "evaluations" in r and isinstance(r["evaluations"], list):
                for ev in r["evaluations"]:
                    yield CanonicalEvaluationItem(
                        item_id=ev.get("item_id", f"EVAL-{r.get('document_id', 'DOC')}"),
                        document_id=r.get("document_id", ev.get("document_id")),
                        task=ev.get("task", "citation_validation"),
                        input=ev.get("input", {}),
                        ground_truth=ev.get("ground_truth", {}),
                        evidence=ev.get("evidence", []),
                        annotation_version=ev.get("annotation_version", "1.0.0"),
                    )
