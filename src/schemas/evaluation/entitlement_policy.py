"""
src/schemas/evaluation/entitlement_policy.py
============================================
Pydantic Schemas and Data Models for Evaluation Entitlement Policies.
Enforces declarative policy constraints, status immutability, and validation.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from .entitlement_catalogue import (
    ADMIN_FEATURES,
    ADMIN_PERMISSIONS,
    ALL_CANONICAL_FEATURES,
    normalize_feature,
)


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class EvaluationPolicyLimits(BaseModel):
    documents_per_license: int = Field(default=20, ge=1, le=1000)
    max_file_size_bytes: int = Field(default=10_485_760, ge=1024, le=104_857_600)  # 10MB
    storage_bytes: int = Field(default=104_857_600, ge=1024, le=1_073_741_824)    # 100MB
    queries_per_license: int = Field(default=100, ge=0, le=10_000)
    comparisons_per_license: int = Field(default=0, ge=0, le=1000)
    concurrent_jobs: int = Field(default=2, ge=1, le=10)


class EvaluationPolicyDocument(BaseModel):
    policy_key: str = Field(..., min_length=3, max_length=64)
    version: str = Field(..., min_length=1, max_length=16)
    features: Dict[str, bool] = Field(default_factory=dict)
    limits: EvaluationPolicyLimits = Field(default_factory=EvaluationPolicyLimits)

    @field_validator("features")
    @classmethod
    def validate_features_catalogue(cls, v: Dict[str, bool]) -> Dict[str, bool]:
        validated = {}
        for feat, enabled in v.items():
            norm = normalize_feature(feat)
            if norm not in ALL_CANONICAL_FEATURES:
                raise ValueError(f"Unknown feature '{feat}' in policy catalogue")
            # ENT-015: Evaluator policy must never contain administrative features
            if norm in ADMIN_FEATURES and enabled:
                raise ValueError(f"Administrative feature '{feat}' cannot be enabled in evaluator policy")
            validated[norm] = bool(enabled)
        return validated

    @model_validator(mode="after")
    def validate_not_admin_permission(self) -> EvaluationPolicyDocument:
        for feat, enabled in self.features.items():
            if feat in ADMIN_PERMISSIONS or feat.startswith("admin."):
                if enabled:
                    raise ValueError(f"Administrative permission '{feat}' forbidden in evaluator policy")
        return self


class EvaluationEntitlementPolicy(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    policy_key: str
    version: str
    status: PolicyStatus = PolicyStatus.DRAFT
    policy_document: EvaluationPolicyDocument
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None


class EvaluationEntitlementOverride(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    license_id: str
    feature_key: str
    override_enabled: bool
    reason_code: str = Field(..., min_length=3)
    issued_by_admin: str = Field(..., min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None

    @field_validator("feature_key")
    @classmethod
    def validate_override_feature(cls, v: str) -> str:
        norm = normalize_feature(v)
        if norm in ADMIN_FEATURES:
            raise ValueError(f"Administrative feature '{v}' cannot be granted via evaluator override")
        return norm

    def is_expired(self, at_time: Optional[datetime] = None) -> bool:
        if self.valid_until is None:
            return False
        now = at_time or datetime.now(timezone.utc)
        return now >= self.valid_until


class EvaluationEntitlementAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    license_id: str
    evaluator_id: str
    tenant_id: str
    policy_key: str
    policy_version: str
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None
