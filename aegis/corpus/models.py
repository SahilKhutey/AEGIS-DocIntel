"""
aegis.corpus.models
===================
Pydantic data models for corpus governance, source registries,
licence metadata, permissions matrices, and acquisition decisions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class PermissionValue(str, Enum):
    YES = "YES"
    NO = "NO"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


class ReviewStatus(str, Enum):
    APPROVED = "APPROVED"
    CONDITIONAL = "CONDITIONAL"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class ProvenanceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class PermissionsRecord(BaseModel):
    """Fine-grained activity permissions."""
    download_and_retain: PermissionValue = PermissionValue.UNKNOWN
    parse_and_extract: PermissionValue = PermissionValue.UNKNOWN
    use_in_evaluation: PermissionValue = PermissionValue.UNKNOWN
    use_for_training: PermissionValue = PermissionValue.UNKNOWN
    publish_derived_annotations: PermissionValue = PermissionValue.UNKNOWN
    redistribute_original: PermissionValue = PermissionValue.UNKNOWN
    redistribute_transformed: PermissionValue = PermissionValue.UNKNOWN


class LicenceRecord(BaseModel):
    """Licence registry entry."""
    licence_id: str = Field(..., pattern=r"^LIC-[A-Z0-9_-]+$")
    name: str = Field(..., min_length=2)
    spdx_identifier: Optional[str] = None
    official_url: str = Field(...)
    rights_holder: str = Field(...)
    attribution_required: bool = True
    attribution_text: Optional[str] = None
    permissions: PermissionsRecord
    legal_review_status: ReviewStatus = ReviewStatus.PENDING
    reviewer: Optional[str] = None
    review_date: Optional[str] = None
    notes: Optional[str] = None


class SourceRecord(BaseModel):
    """Source registry entry."""
    source_id: str = Field(..., pattern=r"^SRC-[A-Z0-9_-]+$")
    source_name: str = Field(..., min_length=2)
    provider: str = Field(..., min_length=2)
    source_url: str = Field(...)
    access_url: Optional[str] = None
    source_type: str = Field(...)
    document_types: List[str] = Field(default_factory=list)
    language: List[str] = Field(default_factory=lambda: ["en"])
    geographic_scope: str = "GLOBAL"
    access_method: str = "direct"
    date_accessed: Optional[str] = None
    source_version: Optional[str] = None
    licence_id: str = Field(..., pattern=r"^LIC-[A-Z0-9_-]+$")
    provenance_status: ProvenanceStatus = ProvenanceStatus.PENDING
    notes: Optional[str] = None


class AcquisitionDecision(BaseModel):
    """Formal acquisition approval decision."""
    decision_id: str = Field(..., pattern=r"^DEC-[A-Z0-9_-]+$")
    source_id: str = Field(..., pattern=r"^SRC-[A-Z0-9_-]+$")
    dataset_id: Optional[str] = None
    status: ReviewStatus = ReviewStatus.PENDING
    permitted_uses: List[str] = Field(default_factory=list)
    prohibited_uses: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    approved_by: str = Field(...)
    approved_at: str = Field(...)
    justification: Optional[str] = None
