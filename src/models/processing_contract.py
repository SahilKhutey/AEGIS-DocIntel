"""
AEGIS-DocIntel — Canonical Document Processing Contracts
=========================================================
Implements Section 3.3 of PROT-FINAL-10 Product Development Sprint.
Establishes standardized dataclasses and schemas for document sources,
extracted structural blocks, and processing results across all engines.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class OpaqueStorageReferenceError(ValueError):
    """Raised when an insecure, non-opaque, or client-supplied filesystem path is provided."""
    pass


def validate_opaque_storage_reference(ref: str) -> None:
    """
    Validate that storage_reference is an opaque, internal identifier rather than
    a client-supplied filesystem path (PROT-FINAL-10 Section 3.3 requirement).

    Permitted formats:
    - blob://<opaque-id>
    - s3://<opaque-id>
    - opaque:<uuid-or-hash>
    - urn:amdi:blob:<id>
    - sqlite:blob:<id>

    Prohibited:
    - Path traversal sequences (../, ..\\)
    - Filesystem drive roots (C:, D:)
    - Absolute filesystem paths (/etc, /var, \\Windows)
    """
    if not ref or not isinstance(ref, str):
        raise OpaqueStorageReferenceError("Storage reference cannot be empty")

    trimmed = ref.strip()
    if ".." in trimmed:
        raise OpaqueStorageReferenceError(f"Path traversal detected in storage reference: {ref}")

    # Check for drive letters (e.g., C:\, D:/)
    if re.match(r"^[a-zA-Z]:[\\/]", trimmed):
        raise OpaqueStorageReferenceError(f"Local filesystem drive path prohibited as storage reference: {ref}")

    # Check for raw absolute paths
    if trimmed.startswith("/") or trimmed.startswith("\\"):
        raise OpaqueStorageReferenceError(f"Raw absolute filesystem path prohibited as storage reference: {ref}")

    # Permitted URI schemes for opaque internal storage
    valid_prefixes = ("blob://", "s3://", "opaque:", "urn:amdi:", "sqlite:blob:", "mem://")
    if not any(trimmed.startswith(prefix) for prefix in valid_prefixes):
        raise OpaqueStorageReferenceError(
            f"Storage reference '{ref}' is not an authorized opaque identifier. "
            f"Must start with one of: {valid_prefixes}"
        )


@dataclass(frozen=True, slots=True)
class DocumentSource:
    """Canonical document source metadata (PROT-FINAL-10 Section 3.3)."""
    document_id: str
    tenant_id: str
    filename: str
    media_type: str
    checksum_sha256: str
    storage_reference: str

    def __post_init__(self):
        validate_opaque_storage_reference(self.storage_reference)
        if len(self.checksum_sha256) != 64:
            raise ValueError(f"checksum_sha256 must be a 64-character hex string, got {len(self.checksum_sha256)}")


@dataclass(frozen=True, slots=True)
class ExtractedBlock:
    """Canonical extracted content block preserving layout provenance (PROT-FINAL-10 Section 3.3)."""
    block_id: str
    text: str
    block_type: str  # paragraph, heading, table, header, footer, list_item, code
    page_number: Optional[int] = None
    section_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "text": self.text,
            "block_type": self.block_type,
            "page_number": self.page_number,
            "section_path": list(self.section_path),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Canonical processing output contract across all extraction & parsing engines."""
    document_id: str
    pipeline_version: str
    status: str
    blocks: List[ExtractedBlock] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "READY" and len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "pipeline_version": self.pipeline_version,
            "status": self.status,
            "blocks": [b.to_dict() for b in self.blocks],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }
