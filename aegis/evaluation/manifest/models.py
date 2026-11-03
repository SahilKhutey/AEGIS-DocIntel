"""
aegis.evaluation.manifest.models
================================
Typed models representing evaluation manifests.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetSpec(BaseModel):
    """Specification of an evaluation dataset with cryptographic integrity."""
    path: str = Field(..., description="Relative or absolute path to dataset")
    sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$", description="SHA-256 digest")
    format: str = Field("jsonl", description="Dataset file format: jsonl, json, csv")
    item_count: Optional[int] = Field(None, ge=0, description="Expected item count")


class TaskSpec(BaseModel):
    """Evaluation task specification referencing a dataset and target engine."""
    dataset: str = Field(..., description="Dataset key reference")
    engine: str = Field(..., description="Engine/evaluator name")
    metrics: List[str] = Field(..., description="Metrics to compute")


class MetricThreshold(BaseModel):
    """Quality gate threshold for a given evaluation metric."""
    min_value: Optional[float] = Field(None, description="Minimum acceptable value")
    max_value: Optional[float] = Field(None, description="Maximum acceptable value")
    strict: bool = Field(True, description="Whether failure halts pipeline")


class EvaluationManifest(BaseModel):
    """Root model for an evaluation manifest."""
    schema_version: str = Field("1.0.0", pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    manifest_id: str = Field(..., min_length=3)
    name: str = Field(..., min_length=3)
    target_domain: str = Field(...)
    description: Optional[str] = None
    datasets: Dict[str, DatasetSpec] = Field(default_factory=dict)
    tasks: Dict[str, TaskSpec] = Field(default_factory=dict)
    quality_gates: Dict[str, MetricThreshold] = Field(default_factory=dict)
