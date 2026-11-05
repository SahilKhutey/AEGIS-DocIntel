"""
aegis.corpus.adapters.cord
==========================
Adapter for the Consolidated Receipt Dataset (CORD) for Post-OCR Parsing format.
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


def _quad_to_bbox(quad: Dict[str, Any]) -> List[float]:
    xs = [quad.get(f"x{i}", 0.0) for i in range(1, 5)]
    ys = [quad.get(f"y{i}", 0.0) for i in range(1, 5)]
    return [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]


class CORDAdapter(DatasetAdapter):
    """Adapter for CORD receipt understanding dataset."""

    @property
    def adapter_name(self) -> str:
        return "CORD"

    @property
    def supported_formats(self) -> List[str]:
        return [".json", "cord"]

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
            if isinstance(data, dict) and ("valid_line" in data or "receipt" in data):
                return True
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "valid_line" in data[0]:
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
            if "valid_line" in data:
                return [{"receipt_id": p.stem, "valid_line": data["valid_line"], "meta": data.get("meta", {})}]
            return [{"receipt_id": p.stem, "valid_line": [], "meta": {}}]
        if isinstance(data, list):
            res = []
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    vl = item.get("valid_line", [])
                    rid = item.get("receipt_id", item.get("id", f"{p.stem}_{idx}"))
                    res.append({"receipt_id": rid, "valid_line": vl, "meta": item.get("meta", {})})
            return res
        return []

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        files = self._get_files(path)
        dataset_id = kwargs.get("dataset_id", "CORD").upper()
        seen = set()

        for f in files:
            receipts = self._parse_file(f)
            for r in receipts:
                raw_id = str(r["receipt_id"])
                doc_id = f"CORD_{raw_id.upper().replace('-', '_')}"
                if doc_id in seen:
                    continue
                seen.add(doc_id)

                sha256 = hashlib.sha256(doc_id.encode("utf-8")).hexdigest()
                yield CanonicalDocument(
                    document_id=doc_id,
                    source_id="SRC-CORD",
                    dataset_id=dataset_id,
                    content=ContentInfo(
                        uri=f"images/{raw_id}.png",
                        format="image/png",
                        sha256=sha256,
                    ),
                    metadata=MetadataInfo(
                        title=f"CORD Receipt {doc_id}",
                        document_type="receipt",
                        language=["en", "id"],
                        page_count=1,
                    ),
                    rights=RightsInfo(
                        licence_id="LIC-CC-BY-4-001",
                        status="APPROVED",
                        attribution_required=True,
                        attribution_text="CORD dataset, Clova AI / NAVER Corp, 2019.",
                    ),
                )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        files = self._get_files(path)
        for f in files:
            receipts = self._parse_file(f)
            for r in receipts:
                raw_id = str(r["receipt_id"])
                doc_id = f"CORD_{raw_id.upper().replace('-', '_')}"
                valid_lines = r.get("valid_line", [])

                bboxes: List[BoundingBoxItem] = []
                line_labels: List[Dict[str, Any]] = []

                for line in valid_lines:
                    cat = line.get("category", "other")
                    words = line.get("words", [])
                    line_text = " ".join([w.get("text", "") for w in words])

                    for w in words:
                        text = w.get("text", "")
                        if "quad" in w:
                            bbox = _quad_to_bbox(w["quad"])
                        elif "box" in w:
                            bbox = [float(x) for x in w["box"]]
                        else:
                            bbox = [0.0, 0.0, 0.0, 0.0]

                        bboxes.append(BoundingBoxItem(
                            page=1,
                            bbox=bbox,
                            category=cat,
                            text=text,
                        ))

                    line_labels.append({
                        "category": cat,
                        "text": line_text,
                    })

                yield CanonicalAnnotation(
                    annotation_id=f"ANNO-CORD-{doc_id}",
                    document_id=doc_id,
                    task="entity_extraction",
                    schema_version="1.0.0",
                    labels={"lines": line_labels},
                    bounding_boxes=bboxes,
                )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        files = self._get_files(path)
        for f in files:
            receipts = self._parse_file(f)
            for r in receipts:
                raw_id = str(r["receipt_id"])
                doc_id = f"CORD_{raw_id.upper().replace('-', '_')}"
                valid_lines = r.get("valid_line", [])

                totals = [l.get("text", "") for l in valid_lines if "total" in l.get("category", "")]
                yield CanonicalEvaluationItem(
                    item_id=f"EVAL-CORD-{doc_id}",
                    document_id=doc_id,
                    task="entity_extraction",
                    input={"document_id": doc_id, "target": "total_extraction"},
                    ground_truth={"totals": totals, "line_count": len(valid_lines)},
                    evidence=[{"page": 1}],
                    annotation_version="1.0.0",
                )
