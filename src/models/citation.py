"""
src/models/citation.py
======================
Canonical Citation Reference model, claim-citation linking, and multi-layer
citation precision verification (L1..L5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator


class CitationReference(BaseModel):
    """
    L1 Canonical Citation Reference model.
    Validates structural integrity, identifier presence, and format.
    """
    citation_id: str = Field(..., min_length=1, description="Unique identifier for citation")
    document_id: str = Field(..., min_length=1, description="Target document identifier")
    document_version: Optional[str] = Field(None, description="Document revision/version tag")
    page_number: Optional[int] = Field(None, ge=1, description="1-indexed document page number")
    section_id: Optional[str] = Field(None, description="Section or heading identifier")
    chunk_id: Optional[str] = Field(None, min_length=1, description="Evidence chunk identifier")
    quoted_text: Optional[str] = Field(None, description="Exact or normalized quoted excerpt")
    source_uri: Optional[str] = Field(None, description="Source URI or storage path")
    claim_id: str = Field("claim_default", description="Associated claim identifier")

    @field_validator("citation_id", "document_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("ID fields cannot be blank")
        return v.strip()


class ClaimVerificationItem(BaseModel):
    """Claim and its associated citation links."""
    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=1)
    citations: List[CitationReference] = Field(default_factory=list)
    expected_supporting: bool = True


@dataclass
class CitationMetrics:
    """Explicit citation verification metrics."""
    precision: float              # P_c = supported / evaluated
    coverage: float               # C_c = claims with supporting cit / total claims
    resolution_rate: float        # R_c = resolved / total citations
    attribution_accuracy: float   # A_c = correct source attribution / total evaluated
    total_claims: int
    supported_claims: int
    total_citations: int
    resolved_citations: int
    supported_citations: int
    correctly_attributed: int


@dataclass
class CitationGateResult:
    """Result of citation precision gate evaluation."""
    passed: bool
    metrics: CitationMetrics
    unsupported_claims: List[str]
    unresolved_citations: List[str]
    attribution_errors: List[str]
    details: str = ""


class CitationEvaluator:
    """
    Evaluates citation precision across 5 layers:
    L1: Syntax & structure (schema validation)
    L2: Source existence (document exists in evidence pool)
    L3: Location precision (page / chunk resolution and alignment)
    L4: Claim support (evidence semantic / lexical grounding)
    L5: Attribution accuracy (version, document ID consistency)
    """

    @classmethod
    def verify_claim_support(cls, claim_text: str, evidence_text: str) -> bool:
        """
        Determines if evidence text supports the claim.
        Employs normalized lexical overlap, token subset entailment,
        and contradictory value detection (dates, numbers, entities).
        """
        if not evidence_text or not claim_text:
            return False

        norm_claim = claim_text.strip().lower()
        norm_ev = evidence_text.strip().lower()

        # Direct containment
        if norm_claim in norm_ev or norm_ev in norm_claim:
            return True

        # Extract numerical tokens (percentages, amounts, years)
        num_claim = set(re.findall(r"\b\d+(?:[\.,]\d+)?%?\b", norm_claim))
        num_ev = set(re.findall(r"\b\d+(?:[\.,]\d+)?%?\b", norm_ev))

        # If claim asserts numbers that do not appear in evidence, reject support
        if num_claim and not num_claim.issubset(num_ev):
            return False

        # Token set overlap for content words
        claim_words = set(re.findall(r"\b[a-z]{3,}\b", norm_claim))
        ev_words = set(re.findall(r"\b[a-z]{3,}\b", norm_ev))
        if not claim_words:
            return True

        overlap = len(claim_words & ev_words) / len(claim_words)
        return overlap >= 0.50

    @classmethod
    def evaluate(
        cls,
        claims: List[ClaimVerificationItem],
        retrieved_evidence: List[Any],
        min_precision: float = 0.90,
        min_coverage: float = 0.90,
        min_resolution_rate: float = 1.0,
        min_attribution_accuracy: float = 0.95,
    ) -> CitationGateResult:
        # Index evidence by doc_id and chunk_id
        chunk_map: Dict[str, Any] = {}
        doc_map: Dict[str, List[Any]] = {}

        for ev in retrieved_evidence:
            doc_id = getattr(ev, "document_id", None) or getattr(ev, "doc_id", None)
            chunk_id = getattr(ev, "chunk_id", None)
            if chunk_id:
                chunk_map[chunk_id] = ev
            if doc_id:
                doc_map.setdefault(doc_id, []).append(ev)

        total_citations = 0
        resolved_citations = 0
        supported_citations = 0
        correctly_attributed = 0

        unresolved_citations_list = []
        unsupported_claims_list = []
        attribution_errors_list = []

        total_claims = len(claims)
        supported_claims = 0

        for claim_item in claims:
            claim_has_valid_supporting_citation = False

            if not claim_item.citations:
                unsupported_claims_list.append(f"Claim '{claim_item.claim_id}': No citations provided")
                continue

            for cit in claim_item.citations:
                total_citations += 1

                # L2 Source existence
                if cit.document_id not in doc_map:
                    unresolved_citations_list.append(
                        f"Citation '{cit.citation_id}': Document '{cit.document_id}' not found in evidence pool"
                    )
                    continue

                # L3 Location precision
                ev_matched = None
                if cit.chunk_id:
                    if cit.chunk_id in chunk_map:
                        ev_matched = chunk_map[cit.chunk_id]
                    else:
                        unresolved_citations_list.append(
                            f"Citation '{cit.citation_id}': Chunk '{cit.chunk_id}' not found in evidence pool"
                        )
                        continue
                else:
                    doc_evs = doc_map.get(cit.document_id, [])
                    if cit.page_number is not None:
                        for dev in doc_evs:
                            if getattr(dev, "page_number", None) == cit.page_number:
                                ev_matched = dev
                                break
                    if not ev_matched and doc_evs:
                        ev_matched = doc_evs[0]

                if not ev_matched:
                    unresolved_citations_list.append(
                        f"Citation '{cit.citation_id}': Location chunk='{cit.chunk_id}' page='{cit.page_number}' unresolved"
                    )
                    continue

                # Check page alignment if both citation and evidence specify page_number
                ev_page = getattr(ev_matched, "page_number", None)
                if cit.page_number is not None and ev_page is not None and cit.page_number != ev_page:
                    unresolved_citations_list.append(
                        f"Citation '{cit.citation_id}': Page mismatch (cited page {cit.page_number} != evidence page {ev_page})"
                    )
                    continue

                resolved_citations += 1

                # L5 Attribution accuracy
                ev_doc = getattr(ev_matched, "document_id", None) or getattr(ev_matched, "doc_id", None)
                if ev_doc != cit.document_id:
                    attribution_errors_list.append(
                        f"Citation '{cit.citation_id}': Attributed to '{cit.document_id}' but chunk resolved from '{ev_doc}'"
                    )
                    continue

                ev_version = getattr(ev_matched, "document_version", None) or getattr(ev_matched, "version", None)
                if cit.document_version and ev_version and cit.document_version != ev_version:
                    attribution_errors_list.append(
                        f"Citation '{cit.citation_id}': Version mismatch ('{cit.document_version}' != '{ev_version}')"
                    )
                    continue

                correctly_attributed += 1

                # L4 Claim support
                ev_text = getattr(ev_matched, "text", "") or getattr(ev_matched, "content", "")
                is_supported = cls.verify_claim_support(claim_item.claim_text, ev_text)

                if is_supported:
                    supported_citations += 1
                    claim_has_valid_supporting_citation = True

            if claim_has_valid_supporting_citation:
                supported_claims += 1
            else:
                unsupported_claims_list.append(claim_item.claim_id)

        # Compute metric ratios
        p_c = (supported_citations / total_citations) if total_citations > 0 else (1.0 if total_claims == 0 else 0.0)
        c_c = (supported_claims / total_claims) if total_claims > 0 else 1.0
        r_c = (resolved_citations / total_citations) if total_citations > 0 else 1.0
        a_c = (correctly_attributed / total_citations) if total_citations > 0 else 1.0

        metrics = CitationMetrics(
            precision=round(p_c, 4),
            coverage=round(c_c, 4),
            resolution_rate=round(r_c, 4),
            attribution_accuracy=round(a_c, 4),
            total_claims=total_claims,
            supported_claims=supported_claims,
            total_citations=total_citations,
            resolved_citations=resolved_citations,
            supported_citations=supported_citations,
            correctly_attributed=correctly_attributed,
        )

        passed = (
            p_c >= min_precision
            and c_c >= min_coverage
            and r_c >= min_resolution_rate
            and a_c >= min_attribution_accuracy
            and len(unresolved_citations_list) == 0
        )

        details = (
            f"Citation Precision: {metrics.precision:.2%} (Gate: {min_precision:.2%}) | "
            f"Coverage: {metrics.coverage:.2%} (Gate: {min_coverage:.2%}) | "
            f"Resolution Rate: {metrics.resolution_rate:.2%} | "
            f"Attribution Accuracy: {metrics.attribution_accuracy:.2%}"
        )

        return CitationGateResult(
            passed=passed,
            metrics=metrics,
            unsupported_claims=unsupported_claims_list,
            unresolved_citations=unresolved_citations_list,
            attribution_errors=attribution_errors_list,
            details=details,
        )
