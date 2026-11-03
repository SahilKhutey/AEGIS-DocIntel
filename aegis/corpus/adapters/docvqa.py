"""
aegis.corpus.adapters.docvqa
============================
Adapter for the Document Visual Question Answering (DocVQA) benchmark format.
"""

from __future__ import annotations

import hashlib
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
    MetadataInfo,
    RightsInfo,
)


class DocVQAAdapter(DatasetAdapter):
    """Adapter for DocVQA dataset files and annotations."""

    @property
    def adapter_name(self) -> str:
        return "DocVQA"

    @property
    def supported_formats(self) -> List[str]:
        return [".json", "docvqa"]

    def validate_source(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            json_files = list(p.glob("*.json"))
            if not json_files:
                return False
            p = json_files[0]

        if not p.is_file() or p.suffix.lower() != ".json":
            return False

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and ("data" in data or "dataset_name" in data):
                return True
            if isinstance(data, list) and len(data) > 0 and ("question" in data[0] or "questionId" in data[0]):
                return True
        except Exception:
            return False
        return False

    def _resolve_data(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        p = Path(path)
        if p.is_dir():
            json_files = list(p.glob("*.json"))
            if not json_files:
                return []
            p = json_files[0]
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            return raw.get("data", [])
        if isinstance(raw, list):
            return raw
        return []

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        items = self._resolve_data(path)
        dataset_id = kwargs.get("dataset_id", "DOCVQA").upper()
        seen_docs = set()

        for item in items:
            raw_doc_id = item.get("ucsf_document_id") or item.get("docId") or item.get("image") or f"doc_{item.get('questionId', '0')}"
            clean_doc_id = f"DOCVQA_{Path(str(raw_doc_id)).stem.upper().replace('-', '_')}"
            if clean_doc_id in seen_docs:
                continue
            seen_docs.add(clean_doc_id)

            img_path = item.get("image", f"{clean_doc_id}.png")
            content_hash = hashlib.sha256(clean_doc_id.encode("utf-8")).hexdigest()

            yield CanonicalDocument(
                document_id=clean_doc_id,
                source_id="SRC-DOCVQA",
                dataset_id=dataset_id,
                content=ContentInfo(
                    uri=img_path,
                    format="image/png" if img_path.endswith(".png") else "application/pdf",
                    sha256=content_hash,
                    size_bytes=item.get("size_bytes", 1024),
                ),
                metadata=MetadataInfo(
                    title=f"DocVQA Document {clean_doc_id}",
                    document_type="form_or_report",
                    language=["en"],
                    page_count=item.get("page_count", 1),
                ),
                rights=RightsInfo(
                    licence_id="LIC-DOCVQA-CHALLENGE-001",
                    status="CONDITIONAL",
                    attribution_required=True,
                    attribution_text="DocVQA Challenge, CVC Barcelona / UCSF Industry Documents Library.",
                ),
            )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        items = self._resolve_data(path)
        for idx, item in enumerate(items):
            raw_doc_id = item.get("ucsf_document_id") or item.get("docId") or item.get("image") or f"doc_{item.get('questionId', idx)}"
            clean_doc_id = f"DOCVQA_{Path(str(raw_doc_id)).stem.upper().replace('-', '_')}"
            qid = str(item.get("questionId", idx))

            bboxes = []
            if "ocr_boxes" in item and "ocr_tokens" in item:
                for box, token in zip(item["ocr_boxes"], item["ocr_tokens"]):
                    if len(box) == 4:
                        bboxes.append(BoundingBoxItem(page=1, bbox=[float(c) for c in box], category="token", text=str(token)))

            yield CanonicalAnnotation(
                annotation_id=f"ANNO-DOCVQA-{qid}",
                document_id=clean_doc_id,
                task="question_answering",
                schema_version="1.0.0",
                labels={
                    "question": item.get("question", ""),
                    "answers": item.get("answers", []),
                },
                bounding_boxes=bboxes,
            )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        items = self._resolve_data(path)
        for idx, item in enumerate(items):
            raw_doc_id = item.get("ucsf_document_id") or item.get("docId") or item.get("image") or f"doc_{item.get('questionId', idx)}"
            clean_doc_id = f"DOCVQA_{Path(str(raw_doc_id)).stem.upper().replace('-', '_')}"
            qid = str(item.get("questionId", idx))

            yield CanonicalEvaluationItem(
                item_id=f"EVAL-DOCVQA-{qid}",
                document_id=clean_doc_id,
                task="question_answering",
                input={"question": item.get("question", "")},
                ground_truth={"answers": item.get("answers", [])},
                evidence=[{"page": 1, "image": item.get("image", "")}],
                annotation_version="1.0.0",
            )
