"""
aegis.corpus.independent.inventory
==================================
Independent public document catalog parser and JSONL streaming exporter.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from pydantic import BaseModel, Field


class DocumentRecord(BaseModel):
    document_id: str
    source_id: str
    dataset_id: str
    category: str
    title: str
    publisher: str
    original_url: str
    version: str = "1.0"
    file_format: str = "pdf"
    pages_estimate: int = 1
    sha256: str
    licence_id: str
    rights_status: str = "APPROVED"


SOURCE_MAP = {
    "DocLayNet": ("SRC-DOCLAYNET-001", "LIC-CDLA-PERMISSIVE-001"),
    "PubLayNet": ("SRC-PUBLAYNET-001", "LIC-CDLA-PERMISSIVE-001"),
    "PubTabNet": ("SRC-PUBTABNET-001", "LIC-CDLA-PERMISSIVE-001"),
    "FUNSD": ("SRC-FUNSD-001", "LIC-FUNSD-ACAD-001"),
    "DocVQA": ("SRC-DOCVQA-001", "LIC-DOCVQA-CHALLENGE-001"),
    "World Bank Documents": ("SRC-WORLDBANK-001", "LIC-CC-BY-4-001"),
    "SEC EDGAR": ("SRC-SEC-EDGAR-001", "LIC-USGOV-PD-001"),
    "India OGD Reports": ("SRC-OGD-INDIA-001", "LIC-GODL-INDIA-001"),
    "arXiv Technical Papers": ("SRC-ARXIV-001", "LIC-ARXIV-OA-001"),
    "AEGIS Adversarial Fixtures": ("SRC-AEGIS-ADV-001", "LIC-APACHE-2-001"),
}


class IndependentDocumentInventory:
    """Parses manifest.csv and streams canonical document records."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.documents: Dict[str, DocumentRecord] = {}

    def load_from_manifest_csv(self, csv_path: Path | str | None = None) -> List[DocumentRecord]:
        path = (
            Path(csv_path)
            if csv_path
            else self.repo_root / "audit" / "corpus" / "manifest.csv"
        )
        if not path.exists():
            raise FileNotFoundError(f"Corpus manifest not found at {path}")

        records: List[DocumentRecord] = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get("doc_id", "").strip()
                repo = row.get("source_repository", "").strip()
                src_id, lic_id = SOURCE_MAP.get(repo, ("SRC-UNKNOWN-001", "LIC-UNKNOWN-001"))

                rec = DocumentRecord(
                    document_id=doc_id,
                    source_id=src_id,
                    dataset_id=f"DATASET-{repo.upper().replace(' ', '_')}",
                    category=row.get("category", "General").strip(),
                    title=row.get("title", "").strip(),
                    publisher=repo,
                    original_url=row.get("source_url", "").strip(),
                    version=row.get("version", "1.0").strip(),
                    file_format=row.get("format", "PDF").strip().lower(),
                    pages_estimate=int(row.get("pages_estimate") or 1),
                    sha256=row.get("checksum_sha256", "").strip(),
                    licence_id=lic_id,
                    rights_status="APPROVED" if "PERMISSIVE" in lic_id or "PD" in lic_id or "CC" in lic_id or "APACHE" in lic_id or "GODL" in lic_id else "CONDITIONAL",
                )
                self.documents[doc_id] = rec
                records.append(rec)

        return records

    def export_jsonl(self, output_path: Path | str) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            for doc in self.documents.values():
                f.write(doc.model_dump_json() + "\n")
