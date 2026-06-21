"""
AMDI-OS Verification Engine
============================

Final validation layer before AI-agent responses reach the user.

Capabilities:
    - Citation Verification   : confirm citations match source documents
    - Fact Verification       : verify factual claims
    - Confidence Scoring      : aggregate response confidence
    - Hallucination Detection : detect fabricated content

Mathematical Foundation:
    Citation accuracy:
        CA = correct_citations / total_citations

    Fact accuracy:
        FA = verified_facts / total_facts

    Hallucination rate:
        HR = false_statements / total_statements

    Composite confidence:
        C = w_c·CA + w_f·FA + w_h·(1 - HR) + w_e·EV

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .verification_engine import VerificationEngine, VerificationReport
from .citation_verifier import (
    CitationVerifier,
    CitationCheckResult,
    CitationMatch,
)
from .fact_verifier import (
    FactVerifier,
    FactCheckResult,
    FactClaim,
)
from .confidence_scorer import (
    ConfidenceScorer,
    ConfidenceScore,
)
from .hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
    HallucinationIndicator,
)
from .consistency_checker import ConsistencyChecker, ConsistencyResult
from .source_verifier import SourceVerifier, SourceCheckResult
from .verification_report import (
    VerificationReportData,
    VerificationMetrics,
)
from .exceptions import (
    VerificationEngineError,
    CitationMissingError,
    FactMismatchError,
    ConfidenceThresholdError,
    HallucinationDetectedError,
)

__all__ = [
    "VerificationEngine",
    "VerificationReport",
    "CitationVerifier",
    "CitationCheckResult",
    "CitationMatch",
    "FactVerifier",
    "FactCheckResult",
    "FactClaim",
    "ConfidenceScorer",
    "ConfidenceScore",
    "HallucinationDetector",
    "HallucinationResult",
    "HallucinationIndicator",
    "ConsistencyChecker",
    "ConsistencyResult",
    "SourceVerifier",
    "SourceCheckResult",
    "VerificationReportData",
    "VerificationMetrics",
    "VerificationEngineError",
    "CitationMissingError",
    "FactMismatchError",
    "ConfidenceThresholdError",
    "HallucinationDetectedError",
]

__version__ = "1.0.0"
