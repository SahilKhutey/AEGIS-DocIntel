"""
aegis.corpus.adapters.publaynet
===============================
Adapter for PubLayNet document layout detection dataset (COCO JSON format).
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


class PubLayNetAdapter(DatasetAdapter):
    """Adapter for PubLayNet document layout analysis format."""

    DEFAULT_CATEGORIES = {
        1: "text",
        2: "title",
        3: "list",
        4: "table",
        5: "figure",
    }

    @property
    def adapter_name(self) -> str:
        return "PubLayNet"

    @property
    def supported_formats(self) -> List[str]:
        return [".json", "publaynet", "coco"]

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
            if isinstance(data, dict) and "images" in data and "annotations" in data:
                return True
        except Exception:
            return False
        return False

    def _load_coco_data(self, path: Union[str, Path]) -> Dict[str, Any]:
        p = Path(path)
        if p.is_dir():
            json_files = list(p.glob("*.json"))
            if not json_files:
                return {"images": [], "annotations": [], "categories": []}
            p = json_files[0]
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        data = self._load_coco_data(path)
        dataset_id = kwargs.get("dataset_id", "PUBLAYNET").upper()
        images = data.get("images", [])

        for img in images:
            img_id = str(img.get("id"))
            file_name = img.get("file_name", f"{img_id}.jpg")
            doc_id = f"PUBLAYNET_{Path(file_name).stem.upper().replace('-', '_')}"
            sha256 = hashlib.sha256(doc_id.encode("utf-8")).hexdigest()

            yield CanonicalDocument(
                document_id=doc_id,
                source_id="SRC-PUBLAYNET",
                dataset_id=dataset_id,
                content=ContentInfo(
                    uri=file_name,
                    format="image/jpeg" if file_name.endswith((".jpg", ".jpeg")) else "image/png",
                    sha256=sha256,
                    size_bytes=img.get("size_bytes", 2048),
                ),
                metadata=MetadataInfo(
                    title=f"PubLayNet Scientific Article Page {file_name}",
                    document_type="scientific_article",
                    language=["en"],
                    page_count=1,
                    extra={
                        "image_width": img.get("width"),
                        "image_height": img.get("height"),
                    },
                ),
                rights=RightsInfo(
                    licence_id="LIC-CC-BY-4-001",
                    status="APPROVED",
                    attribution_required=True,
                    attribution_text="PubLayNet, IBM Research & PubMed Central Open Access.",
                ),
            )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        data = self._load_coco_data(path)
        images = {img["id"]: img for img in data.get("images", [])}
        categories = {cat["id"]: cat["name"] for cat in data.get("categories", [])}
        if not categories:
            categories = self.DEFAULT_CATEGORIES

        # Group annotations by image_id
        annos_by_image: Dict[Any, List[Dict[str, Any]]] = {}
        for ann in data.get("annotations", []):
            img_id = ann.get("image_id")
            annos_by_image.setdefault(img_id, []).append(ann)

        for img_id, img in images.items():
            file_name = img.get("file_name", f"{img_id}.jpg")
            doc_id = f"PUBLAYNET_{Path(file_name).stem.upper().replace('-', '_')}"
            raw_annos = annos_by_image.get(img_id, [])

            bboxes: List[BoundingBoxItem] = []
            category_counts: Dict[str, int] = {}

            for ann in raw_annos:
                cid = ann.get("category_id")
                cname = categories.get(cid, "text")
                bbox = ann.get("bbox", [0, 0, 0, 0])  # [x, y, w, h]
                if len(bbox) == 4:
                    x0, y0, w, h = [float(v) for v in bbox]
                    x1, y1 = x0 + w, y0 + h
                    bboxes.append(BoundingBoxItem(
                        page=1,
                        bbox=[x0, y0, x1, y1],
                        category=cname,
                    ))
                category_counts[cname] = category_counts.get(cname, 0) + 1

            yield CanonicalAnnotation(
                annotation_id=f"ANNO-PUBLAYNET-{doc_id}",
                document_id=doc_id,
                task="layout_detection",
                schema_version="1.0.0",
                labels={"layout_categories": category_counts, "box_count": len(bboxes)},
                bounding_boxes=bboxes,
            )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        data = self._load_coco_data(path)
        images = {img["id"]: img for img in data.get("images", [])}
        annos_by_image: Dict[Any, List[Dict[str, Any]]] = {}
        for ann in data.get("annotations", []):
            img_id = ann.get("image_id")
            annos_by_image.setdefault(img_id, []).append(ann)

        for img_id, img in images.items():
            file_name = img.get("file_name", f"{img_id}.jpg")
            doc_id = f"PUBLAYNET_{Path(file_name).stem.upper().replace('-', '_')}"
            raw_annos = annos_by_image.get(img_id, [])

            yield CanonicalEvaluationItem(
                item_id=f"EVAL-PUBLAYNET-{doc_id}",
                document_id=doc_id,
                task="layout_detection",
                input={"document_id": doc_id, "width": img.get("width"), "height": img.get("height")},
                ground_truth={"layout_elements_count": len(raw_annos)},
                evidence=[{"page": 1, "image": file_name}],
                annotation_version="1.0.0",
            )
