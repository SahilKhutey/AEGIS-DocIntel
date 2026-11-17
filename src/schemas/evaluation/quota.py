"""
AEGIS-DocIntel Evaluation Quota Schema (PROT-04 WP-04.06)
Defines canonical quota categories, periods, units, and policy models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class QuotaDimension(str, Enum):
    STORAGE = "storage"
    DOCUMENTS = "documents"
    UPLOAD = "upload"
    PARSING = "parsing"
    OCR = "ocr"
    QUERIES = "queries"
    COMPARISONS = "comparisons"
    LLM_TOKENS = "llm_tokens"
    API_REQUESTS = "api_requests"
    CONCURRENT_JOBS = "concurrent_jobs"
    EXPORTS = "exports"
    PROCESSING_TIME = "processing_time"


class QuotaPeriod(str, Enum):
    LIFETIME = "lifetime"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ROLLING = "rolling"
    CONCURRENT = "concurrent"
    PER_OPERATION = "per_operation"


class QuotaUnit(str, Enum):
    BYTES = "bytes"
    DOCUMENTS = "documents"
    REQUESTS = "requests"
    JOBS = "jobs"
    PAGES = "pages"
    QUERIES = "queries"
    COMPARISONS = "comparisons"
    TOKENS = "tokens"
    EXPORTS = "exports"
    MILLISECONDS = "milliseconds"


DIMENSION_ALLOWED_UNITS: Dict[QuotaDimension, List[QuotaUnit]] = {
    QuotaDimension.STORAGE: [QuotaUnit.BYTES],
    QuotaDimension.DOCUMENTS: [QuotaUnit.DOCUMENTS],
    QuotaDimension.UPLOAD: [QuotaUnit.REQUESTS],
    QuotaDimension.PARSING: [QuotaUnit.JOBS, QuotaUnit.PAGES],
    QuotaDimension.OCR: [QuotaUnit.PAGES],
    QuotaDimension.QUERIES: [QuotaUnit.QUERIES],
    QuotaDimension.COMPARISONS: [QuotaUnit.COMPARISONS],
    QuotaDimension.LLM_TOKENS: [QuotaUnit.TOKENS],
    QuotaDimension.API_REQUESTS: [QuotaUnit.REQUESTS],
    QuotaDimension.CONCURRENT_JOBS: [QuotaUnit.JOBS],
    QuotaDimension.EXPORTS: [QuotaUnit.EXPORTS],
    QuotaDimension.PROCESSING_TIME: [QuotaUnit.MILLISECONDS],
}


class QuotaDefinition(BaseModel):
    dimension: QuotaDimension
    limit: int = Field(ge=0, description="Maximum permitted units; must be non-negative integer")
    period: QuotaPeriod
    unit: QuotaUnit
    rolling_window_seconds: Optional[int] = Field(default=None, ge=1, description="Window size in seconds for rolling period")

    @model_validator(mode="after")
    def validate_dimension_and_unit(self) -> QuotaDefinition:
        allowed = DIMENSION_ALLOWED_UNITS.get(self.dimension)
        if allowed and self.unit not in allowed:
            raise ValueError(
                f"Incompatible unit '{self.unit.value}' for quota dimension '{self.dimension.value}'. Allowed: {[u.value for u in allowed]}"
            )
        if self.period == QuotaPeriod.ROLLING and not self.rolling_window_seconds:
            raise ValueError("Rolling quota period requires 'rolling_window_seconds' to be specified")
        return self


class EvaluationQuotaPolicy(BaseModel):
    policy_key: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = Field(default="DRAFT", description="DRAFT, ACTIVE, or RETIRED")
    quotas: Dict[str, QuotaDefinition]
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    activated_at: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"DRAFT", "ACTIVE", "RETIRED"}
        v_upper = v.upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Invalid policy status '{v}'. Expected one of {valid_statuses}")
        return v_upper

    @field_validator("quotas")
    @classmethod
    def validate_quotas_dict(cls, v: Dict[str, QuotaDefinition]) -> Dict[str, QuotaDefinition]:
        if not v:
            raise ValueError("Evaluation quota policy must contain at least one quota definition")
        for key, definition in v.items():
            if key != definition.dimension.value:
                raise ValueError(
                    f"Quota map key '{key}' does not match dimension definition '{definition.dimension.value}'"
                )
        return v


def get_default_evaluation_basic_quota_policy() -> EvaluationQuotaPolicy:
    """Standard Evaluation Basic tier quota profile."""
    return EvaluationQuotaPolicy(
        policy_key="evaluation-basic",
        version="1.0",
        status="ACTIVE",
        description="AEGIS Evaluation Basic Tier Provisional Quota Policy",
        created_at=datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc),
        activated_at=datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc),
        quotas={
            QuotaDimension.DOCUMENTS.value: QuotaDefinition(
                dimension=QuotaDimension.DOCUMENTS,
                limit=20,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.DOCUMENTS,
            ),
            QuotaDimension.STORAGE.value: QuotaDefinition(
                dimension=QuotaDimension.STORAGE,
                limit=100 * 1024 * 1024,  # 100 MB
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.BYTES,
            ),
            QuotaDimension.QUERIES.value: QuotaDefinition(
                dimension=QuotaDimension.QUERIES,
                limit=100,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.QUERIES,
            ),
            QuotaDimension.COMPARISONS.value: QuotaDefinition(
                dimension=QuotaDimension.COMPARISONS,
                limit=10,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.COMPARISONS,
            ),
            QuotaDimension.API_REQUESTS.value: QuotaDefinition(
                dimension=QuotaDimension.API_REQUESTS,
                limit=1000,
                period=QuotaPeriod.DAILY,
                unit=QuotaUnit.REQUESTS,
            ),
            QuotaDimension.CONCURRENT_JOBS.value: QuotaDefinition(
                dimension=QuotaDimension.CONCURRENT_JOBS,
                limit=2,
                period=QuotaPeriod.CONCURRENT,
                unit=QuotaUnit.JOBS,
            ),
            QuotaDimension.LLM_TOKENS.value: QuotaDefinition(
                dimension=QuotaDimension.LLM_TOKENS,
                limit=50_000,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.TOKENS,
            ),
            QuotaDimension.EXPORTS.value: QuotaDefinition(
                dimension=QuotaDimension.EXPORTS,
                limit=5,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.EXPORTS,
            ),
            QuotaDimension.OCR.value: QuotaDefinition(
                dimension=QuotaDimension.OCR,
                limit=50,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.PAGES,
            ),
        },
    )


def get_default_evaluation_pro_quota_policy() -> EvaluationQuotaPolicy:
    """Standard Evaluation Pro tier quota profile."""
    return EvaluationQuotaPolicy(
        policy_key="evaluation-pro",
        version="1.0",
        status="ACTIVE",
        description="AEGIS Evaluation Pro Tier Expanded Quota Policy",
        created_at=datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc),
        activated_at=datetime(2026, 11, 14, 0, 0, 0, tzinfo=timezone.utc),
        quotas={
            QuotaDimension.DOCUMENTS.value: QuotaDefinition(
                dimension=QuotaDimension.DOCUMENTS,
                limit=50,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.DOCUMENTS,
            ),
            QuotaDimension.STORAGE.value: QuotaDefinition(
                dimension=QuotaDimension.STORAGE,
                limit=500 * 1024 * 1024,  # 500 MB
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.BYTES,
            ),
            QuotaDimension.QUERIES.value: QuotaDefinition(
                dimension=QuotaDimension.QUERIES,
                limit=500,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.QUERIES,
            ),
            QuotaDimension.COMPARISONS.value: QuotaDefinition(
                dimension=QuotaDimension.COMPARISONS,
                limit=50,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.COMPARISONS,
            ),
            QuotaDimension.API_REQUESTS.value: QuotaDefinition(
                dimension=QuotaDimension.API_REQUESTS,
                limit=5000,
                period=QuotaPeriod.DAILY,
                unit=QuotaUnit.REQUESTS,
            ),
            QuotaDimension.CONCURRENT_JOBS.value: QuotaDefinition(
                dimension=QuotaDimension.CONCURRENT_JOBS,
                limit=5,
                period=QuotaPeriod.CONCURRENT,
                unit=QuotaUnit.JOBS,
            ),
            QuotaDimension.LLM_TOKENS.value: QuotaDefinition(
                dimension=QuotaDimension.LLM_TOKENS,
                limit=250_000,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.TOKENS,
            ),
            QuotaDimension.EXPORTS.value: QuotaDefinition(
                dimension=QuotaDimension.EXPORTS,
                limit=25,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.EXPORTS,
            ),
            QuotaDimension.OCR.value: QuotaDefinition(
                dimension=QuotaDimension.OCR,
                limit=200,
                period=QuotaPeriod.LIFETIME,
                unit=QuotaUnit.PAGES,
            ),
        },
    )
