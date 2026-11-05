"""
aegis.corpus.adapters.funsd
===========================
Adapter for the Form Understanding in Noisy Scanned Documents (FUNSD) benchmark format.
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


class FUNSDAdapter(DatasetAdapter):
    """Adapter for FUNSD form understanding annotations."""

    @property
    def adapter_name(self) -> str:
        return "FUNSD"

    @property
    def supported_formats(self) -> List[str]:
        return [".json", "funsd"]

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
            if isinstance(data, dict) and "form" in data:
                return True
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and ("form" in data[0] or "box" in data[0]):
                return True
        except Exception:
            return False
        return False

    def _get_files(self, path: Union[str, Path]) -> List[Path]:
        p = Path(path)
        if p.is_dir():
            return sorted(list(p.glob("*.json")))
        return [p]

    def _parse_file(self, p: Path) -> List[Dict[str, Any]]:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "form" in data:
                return [{"doc_id": p.stem, "form": data["form"]}]
            return [{"doc_id": p.stem, "form": []}]
        if isinstance(data, list):
            res = []
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    form = item.get("form", item if "box" in item else [])
                    doc_id = item.get("id", item.get("doc_id", f"{p.stem}_{idx}"))
                    res.append({"doc_id": doc_id, "form": form})
            return res
        return []

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        files = self._get_files(path)
        dataset_id = kwargs.get("dataset_id", "FUNSD").upper()
        seen = set()

        for f in files:
            docs = self._parse_file(f)
            for d in docs:
                raw_id = str(d["doc_id"])
                doc_id = f"FUNSD_{raw_id.upper().replace('-', '_')}"
                if doc_id in seen:
                    continue
                seen.add(doc_id)

                sha256 = hashlib.sha256(doc_id.encode("utf-8")).hexdigest()
                yield CanonicalDocument(
                    document_id=doc_id,
                    source_id="SRC-FUNSD",
                    dataset_id=dataset_id,
                    content=ContentInfo(
                        uri=f"images/{raw_id}.png",
                        format="image/png",
                        sha256=sha256,
                    ),
                    metadata=MetadataInfo(
                        title=f"FUNSD Scanned Form {doc_id}",
                        document_type="form",
                        language=["en"],
                        page_count=1,
                    ),
                    rights=RightsInfo(
                        licence_id="LIC-FUNSD-ACAD-001",
                        status="CONDITIONAL",
                        attribution_required=True,
                        attribution_text="FUNSD dataset, Guillaume Jaume et al., ICDAR-OST 2019.",
                    ),
                )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        files = self._get_files(path)
        for f in files:
            docs = self._parse_file(f)
            for d in docs:
                raw_id = str(d["doc_id"])
                doc_id = f"FUNSD_{raw_id.upper().replace('-', '_')}"
                form_items = d.get("form", [])

                bboxes: List[BoundingBoxItem] = []
                entities: List[Dict[str, Any]] = []

                for item in form_items:
                    box = item.get("box", [0, 0, 0, 0])
                    category = item.get("label", "other")
                    text = item.get("text", "")
                    linking = item.get("linking", [])
                    item_id = item.get("id")

                    if len(box) == 4:
                        bboxes.append(BoundingBoxItem(
                            page=1,
                            bbox=[float(x) for x in box],
                            category=category,
                            text=text,
                        ))
                    entities.append({
                        "id": item_id,
                        "text": text,
                        "category": category,
                        "box": box,
                        "linking": linking,
                    })

                yield CanonicalAnnotation(
                    annotation_id=f"ANNO-FUNSD-{doc_id}",
                    document_id=doc_id,
                    task="entity_extraction",
                    schema_version="1.0.0",
                    labels={"entities": entities},
                    bounding_boxes=bboxes,
                )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        files = self._get_files(path)
        for f in files:
            docs = self._parse_file(f)
            for d in docs:
                raw_id = str(d["doc_id"])
                doc_id = f"FUNSD_{raw_id.upper().replace('-', '_')}"
                form_items = d.get("form", [])

                # Form key-value extraction item
                questions = [it for it in form_items if it.get("label") == "question"]
                answers = [it for it in form_items if it.get("label") == "answer"]

                yield CanonicalEvaluationItem(
                    item_id=f"EVAL-FUNSD-{doc_id}",
                    document_id=doc_id,
                    task="entity_extraction",
                    input={"document_id": doc_id, "mode": "form_understanding"},
                    ground_truth={
                        "question_count": len(questions),
                        "answer_count": len(answers),
                        "total_elements": len(form_items),
                    },
                    evidence=[{"page": 1}],
                    annotation_version="1.0.0",
                )
