"""
aegis.intelligence.models
=========================
Strongly-typed Pydantic domain models for WP-06 Intelligence capabilities:
retrieval, golden questions, claim citations, answerability, facts, conflicts,
and structured reports.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# 1. Retrieval Models (WP-06.01)
# ==============================================================================

class RetrievalMode(str, Enum):
    LEXICAL = "lexical"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    STRUCTURED = "structured"


class RetrievalItem(BaseModel):
    document_id: str
    chunk_id: str
    page_number: int = Field(ge=1)
    text: str
    rank: int = Field(ge=1)
    score: float
    retrieval_method: str
    source_reference: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    query_id: str
    retrieval_mode: RetrievalMode
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    results: List[RetrievalItem] = Field(default_factory=list)
    latency_ms: float = Field(ge=0.0)


# ==============================================================================
# 2. Golden Question Models (WP-06.02)
# ==============================================================================

class TaskType(str, Enum):
    DIRECT_FACTUAL = "direct_factual"
    ENTITY_EXTRACTION = "entity_extraction"
    NUMERIC_EXTRACTION = "numeric_extraction"
    TEMPORAL_REASONING = "temporal_reasoning"
    TABLE_RETRIEVAL = "table_retrieval"
    MULTI_HOP = "multi_hop"
    CROSS_DOCUMENT = "cross_document"
    SUMMARIZATION = "summarization"
    CITATION_VERIFICATION = "citation_verification"
    UNANSWERABLE = "unanswerable"
    AMBIGUITY_CLARIFICATION = "ambiguity_clarification"
    CONFLICT_ANALYSIS = "conflict_analysis"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class AnswerabilityClass(str, Enum):
    ANSWERABLE = "ANSWERABLE"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    RESTRICTED = "RESTRICTED"


class ExpectedAnswer(BaseModel):
    value: Optional[Union[str, int, float, bool]] = None
    type: str
    unit: Optional[str] = None


class RequiredEvidence(BaseModel):
    document_id: str
    page_number: Optional[int] = None
    region_id: Optional[str] = None
    chunk_id: Optional[str] = None
    evidence_text: str


class QuestionEvaluation(BaseModel):
    answer_match: Literal["exact", "normalized_exact", "numeric_tolerance", "semantic", "abstention"]
    citation_required: bool = True
    all_evidence_required: bool = True


class GoldenQuestion(BaseModel):
    question_id: str
    dataset_version: str = "1.0"
    question: str
    task_type: TaskType
    difficulty: DifficultyLevel
    answerability: AnswerabilityClass
    document_scope: List[str]
    expected_answer: ExpectedAnswer
    accepted_answers: List[str] = Field(default_factory=list)
    required_evidence: List[RequiredEvidence] = Field(default_factory=list)
    evaluation: QuestionEvaluation
    annotation_status: Literal["DRAFT", "REVIEWED", "APPROVED", "DEPRECATED"] = "REVIEWED"
    annotation_version: str = "1.0"
    reviewer: str = "AEGIS-QA-BENCH"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


# ==============================================================================
# 3. Citation & Claim Support Models (WP-06.03)
# ==============================================================================

class SupportLabel(str, Enum):
    SUPPORTS = "SUPPORTS"
    PARTIALLY_SUPPORTS = "PARTIALLY_SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    RELATED_ONLY = "RELATED_ONLY"
    IRRELEVANT = "IRRELEVANT"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


class CitationRef(BaseModel):
    citation_id: str
    document_id: str
    page_number: Optional[int] = None
    region_id: Optional[str] = None
    chunk_id: Optional[str] = None
    support_label: SupportLabel = SupportLabel.SUPPORTS
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    rationale: Optional[str] = None


class ClaimSupportStatus(str, Enum):
    FULLY_SUPPORTED = "FULLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class ClaimItem(BaseModel):
    claim_id: str
    text: str
    citations: List[CitationRef] = Field(default_factory=list)
    support_status: ClaimSupportStatus = ClaimSupportStatus.FULLY_SUPPORTED


class CitationSummary(BaseModel):
    citation_precision: float = Field(ge=0.0, le=1.0)
    claim_support_rate: float = Field(ge=0.0, le=1.0)
    citation_coverage: float = Field(ge=0.0, le=1.0)
    unsupported_claim_rate: float = Field(ge=0.0, le=1.0)
    total_claims: int = 0
    total_citations: int = 0


class ClaimCitationEvaluation(BaseModel):
    answer_id: str
    question_id: Optional[str] = None
    answer_text: str
    claims: List[ClaimItem] = Field(default_factory=list)
    evaluation_summary: CitationSummary


# ==============================================================================
# 4. Answerability Models (WP-06.04)
# ==============================================================================

class AnswerabilityDecision(str, Enum):
    ANSWER = "ANSWER"
    ABSTAIN_NOT_FOUND = "ABSTAIN_NOT_FOUND"
    ABSTAIN_INSUFFICIENT = "ABSTAIN_INSUFFICIENT"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    DISCLOSE_CONFLICT = "DISCLOSE_CONFLICT"
    DENY_RESTRICTED = "DENY_RESTRICTED"


class AnswerabilitySignals(BaseModel):
    retrieved_chunk_count: int = Field(ge=0)
    max_relevance_score: float = Field(ge=0.0)
    source_count: int = Field(ge=0)
    contradiction_detected: bool = False
    missing_required_fields: List[str] = Field(default_factory=list)


class AnswerabilityResult(BaseModel):
    question_id: str
    classification: AnswerabilityClass
    evidence_sufficiency_score: float = Field(ge=0.0, le=1.0)
    decision: AnswerabilityDecision
    signals: AnswerabilitySignals
    explanation: Optional[str] = None


# ==============================================================================
# 5. Fact Models (WP-06.05)
# ==============================================================================

class EntityRef(BaseModel):
    entity_id: str
    name: str
    type: str


class FactObject(BaseModel):
    value: Union[str, int, float, bool]
    raw_value: str
    unit: Optional[str] = None
    data_type: Literal["string", "quantity", "currency", "date", "boolean", "percentage"] = "string"


class FactQualifiers(BaseModel):
    reporting_period: Optional[str] = None
    geographic_scope: Optional[str] = None
    status: Optional[str] = None
    date_precision: Optional[str] = None


class FactEvidence(BaseModel):
    document_id: str
    page_number: Optional[int] = None
    region_id: Optional[str] = None
    chunk_id: Optional[str] = None
    quoted_text: str = ""


class FactItem(BaseModel):
    fact_id: str
    subject: EntityRef
    predicate: str
    object: FactObject
    qualifiers: FactQualifiers = Field(default_factory=FactQualifiers)
    evidence: List[FactEvidence] = Field(default_factory=list)
    extraction_method: Literal["structured_extraction", "regex", "table_cell_extraction", "relation_model"] = "structured_extraction"
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    verification_status: Literal["UNVERIFIED", "VERIFIED", "DISPUTED", "DEPRECATED"] = "UNVERIFIED"


# ==============================================================================
# 6. Conflict Models (WP-06.05)
# ==============================================================================

class ConflictClassification(str, Enum):
    NO_CONFLICT = "NO_CONFLICT"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    DIRECT_CONFLICT = "DIRECT_CONFLICT"
    SCOPE_DIFFERENCE = "SCOPE_DIFFERENCE"
    TEMPORAL_DIFFERENCE = "TEMPORAL_DIFFERENCE"
    UNIT_DIFFERENCE = "UNIT_DIFFERENCE"
    VERSION_DIFFERENCE = "VERSION_DIFFERENCE"
    DEFINITION_DIFFERENCE = "DEFINITION_DIFFERENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ConflictFactRef(BaseModel):
    fact_id: str
    value: Union[str, int, float, bool]
    raw_value: Optional[str] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    document_id: str
    page_number: Optional[int] = None


class ConflictItem(BaseModel):
    conflict_id: str
    subject: str
    predicate: str
    facts: List[ConflictFactRef]
    classification: ConflictClassification
    reason: str
    resolution_status: Literal["UNRESOLVED", "RESOLVED_SUPERSEDED", "RESOLVED_DIFFERENT_SCOPE", "NEEDS_HUMAN_REVIEW"] = "UNRESOLVED"


# ==============================================================================
# 7. Report Models (WP-06.06)
# ==============================================================================

class ReportType(str, Enum):
    DOCUMENT_SUMMARY = "document_summary"
    QUESTION_ANSWER_REPORT = "question_answer_report"
    COMPARATIVE_REPORT = "comparative_report"
    FACT_EXTRACTION_REPORT = "fact_extraction_report"
    CONFLICT_REPORT = "conflict_report"
    AUDIT_REPORT = "audit_report"
    FINANCIAL_REPORT = "financial_report"


class ReportCitation(BaseModel):
    document_id: str
    page_number: Optional[int] = None
    region_id: Optional[str] = None
    chunk_id: Optional[str] = None


class ReportClaim(BaseModel):
    claim_id: str
    text: str
    citations: List[ReportCitation] = Field(default_factory=list)


class ReportSection(BaseModel):
    section_id: str
    heading: str
    summary: Optional[str] = None
    claims: List[ReportClaim] = Field(default_factory=list)


class ReportScope(BaseModel):
    document_ids: List[str]
    questions: List[str] = Field(default_factory=list)


class ReportMetadata(BaseModel):
    evaluation_manifest_id: str = "EVAL-MANIFEST-WP06"
    processing_run_ids: List[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    generator_version: str = "1.0.0"


class ReportItem(BaseModel):
    report_id: str
    report_type: ReportType
    title: str
    scope: ReportScope
    sections: List[ReportSection] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    generation_metadata: ReportMetadata = Field(default_factory=ReportMetadata)
