"""
aegis.processing.provenance.lineage
===================================
Document processing lineage recording source origin, checksums, software versions, and stage logs.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentLineage(BaseModel):
    document_id: str
    original_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    source_id: str
    licence_id: str
    dataset_id: Optional[str] = None
    processing_run_id: str
    pipeline_version: str = "1.0.0"
    configuration_hash: str
    software_versions: Dict[str, str] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    transformation_history: List[Dict[str, Any]] = Field(default_factory=list)

    def record_stage(self, stage_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Append transformation step to lineage audit log."""
        self.transformation_history.append({
            "stage": stage_name,
            "status": status,
            "details": details or {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
