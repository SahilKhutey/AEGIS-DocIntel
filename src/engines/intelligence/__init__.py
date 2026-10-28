"""
src/engines/intelligence/__init__.py
====================================
AEGIS-DocIntel Structured Document Intelligence, Fact Extraction,
and Cross-Document Reasoning Engine.
"""

from src.engines.intelligence.contracts import (
    ComparisonStatus,
    ConflictReport,
    ConflictType,
    DocumentComparisonResult,
    EvidenceSpan,
    ExtractedFact,
    ExtractionResult,
    ExtractionSchema,
    ExtractionStatus,
    FactValueType,
    FieldDefinition,
    PairComparison,
)
from src.engines.intelligence.entity_resolution import (
    EntityResolver,
    normalize_entity_label,
    same_normalized_label,
)
from src.engines.intelligence.normalization import (
    normalize_boolean,
    normalize_currency_amount,
    normalize_date,
    normalize_day_count,
    normalize_unit,
    parse_decimal,
)
from src.engines.intelligence.fact_extractor import (
    BUILTIN_SCHEMAS,
    CONTRACT_TERMS_SCHEMA,
    FINANCIAL_METRICS_SCHEMA,
    FactExtractor,
    build_untrusted_document_envelope,
    verify_quote_in_source,
)
from src.engines.intelligence.comparison import (
    CrossTenantComparisonError,
    DocumentComparator,
)
from src.engines.intelligence.conflict_detection import ConflictDetector
from src.engines.intelligence.fact_store import FactStore
from src.engines.intelligence.service import DocumentIntelligenceService

__all__ = [
    "FactValueType",
    "ComparisonStatus",
    "ConflictType",
    "ExtractionStatus",
    "EvidenceSpan",
    "ExtractedFact",
    "FieldDefinition",
    "ExtractionSchema",
    "ExtractionResult",
    "PairComparison",
    "DocumentComparisonResult",
    "ConflictReport",
    "normalize_entity_label",
    "same_normalized_label",
    "EntityResolver",
    "parse_decimal",
    "normalize_currency_amount",
    "normalize_day_count",
    "normalize_date",
    "normalize_boolean",
    "normalize_unit",
    "FactExtractor",
    "verify_quote_in_source",
    "build_untrusted_document_envelope",
    "BUILTIN_SCHEMAS",
    "FINANCIAL_METRICS_SCHEMA",
    "CONTRACT_TERMS_SCHEMA",
    "DocumentComparator",
    "CrossTenantComparisonError",
    "ConflictDetector",
    "FactStore",
    "DocumentIntelligenceService",
]
