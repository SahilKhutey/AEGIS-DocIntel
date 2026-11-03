"""
aegis.corpus.adapters.generic_pdf
=================================
Adapter for generic PDF files and PDF directory collections.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from aegis.corpus.adapters.base import DatasetAdapter
from aegis.corpus.adapters.models import (
    CanonicalAnnotation,
    CanonicalDocument,
    CanonicalEvaluationItem,
    ContentInfo,
    EvidenceSpan,
    MetadataInfo,
    RightsInfo,
)


def _get_pdf_info(path: Path) -> Dict[str, Any]:
    """Extract page count and basic text from PDF using PyMuPDF or regex fallback."""
    page_count = 1
    sample_text = ""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(path))
        page_count = max(1, len(doc))
        if len(doc) > 0:
            sample_text = doc[0].get_text()[:500]
        doc.close()
    except Exception:
        # Fallback to byte scan for /Count
        try:
            with open(path, "rb") as f:
                content = f.read()
            matches = re.findall(rb"/Count\s+(\d+)", content)
            if matches:
                page_count = max(1, int(matches[-1]))
        except Exception:
            page_count = 1
    return {"page_count": page_count, "sample_text": sample_text}


class GenericPDFAdapter(DatasetAdapter):
    """Adapter for raw PDF documents and directory trees."""

    @property
    def adapter_name(self) -> str:
        return "GenericPDF"

    @property
    def supported_formats(self) -> List[str]:
        return [".pdf", "pdf"]

    def validate_source(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            pdf_files = list(p.glob("*.pdf"))
            return len(pdf_files) > 0
        return p.is_file() and p.suffix.lower() == ".pdf"

    def _get_pdf_paths(self, path: Union[str, Path]) -> List[Path]:
        p = Path(path)
        if p.is_dir():
            return sorted(list(p.glob("*.pdf")))
        if p.is_file() and p.suffix.lower() == ".pdf":
            return [p]
        return []

    def load_documents(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalDocument]:
        pdf_paths = self._get_pdf_paths(path)
        dataset_id = kwargs.get("dataset_id", "GENERIC_PDF").upper()
        source_id = kwargs.get("source_id", "SRC-BENCHMARK-REAL")
        licence_id = kwargs.get("licence_id", "LIC-CC-BY-4-001")

        for p in pdf_paths:
            clean_stem = re.sub(r"[^A-Za-z0-9_]", "_", p.stem).upper()
            doc_id = f"PDF_{clean_stem}"

            # Calculate SHA256 streaming
            hasher = hashlib.sha256()
            size_bytes = 0
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
                    size_bytes += len(chunk)
            digest = hasher.hexdigest()

            info = _get_pdf_info(p)

            yield CanonicalDocument(
                document_id=doc_id,
                source_id=source_id,
                dataset_id=dataset_id,
                content=ContentInfo(
                    uri=str(p.as_posix()),
                    format="application/pdf",
                    sha256=digest,
                    size_bytes=size_bytes,
                ),
                metadata=MetadataInfo(
                    title=f"Document {p.name}",
                    document_type="pdf_document",
                    language=["en"],
                    page_count=info["page_count"],
                    publisher="AEGIS Corpus Collection",
                ),
                rights=RightsInfo(
                    licence_id=licence_id,
                    status="APPROVED",
                    attribution_required=True,
                    attribution_text=f"AEGIS Document Collection: {p.name}",
                ),
                raw_text=info["sample_text"],
            )

    def load_annotations(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalAnnotation]:
        pdf_paths = self._get_pdf_paths(path)
        for p in pdf_paths:
            clean_stem = re.sub(r"[^A-Za-z0-9_]", "_", p.stem).upper()
            doc_id = f"PDF_{clean_stem}"
            info = _get_pdf_info(p)

            yield CanonicalAnnotation(
                annotation_id=f"ANNO-PDF-{doc_id}",
                document_id=doc_id,
                task="document_classification",
                schema_version="1.0.0",
                labels={
                    "format": "application/pdf",
                    "page_count": info["page_count"],
                    "filename": p.name,
                },
                evidence_spans=[
                    EvidenceSpan(page=1, chunk_id="chunk_0", text=info["sample_text"][:200])
                ] if info["sample_text"] else [],
            )

    def load_evaluation_items(self, path: Union[str, Path], **kwargs) -> Iterator[CanonicalEvaluationItem]:
        pdf_paths = self._get_pdf_paths(path)
        for p in pdf_paths:
            clean_stem = re.sub(r"[^A-Za-z0-9_]", "_", p.stem).upper()
            doc_id = f"PDF_{clean_stem}"
            info = _get_pdf_info(p)

            yield CanonicalEvaluationItem(
                item_id=f"EVAL-PDF-{doc_id}",
                document_id=doc_id,
                task="citation_validation",
                input={"document_id": doc_id, "query": f"Verify citation targets in {p.name}"},
                ground_truth={"expected_pages": info["page_count"], "primary_citation_page": 1},
                evidence=[{"page": 1, "target": p.name}],
                annotation_version="1.0.0",
            )
