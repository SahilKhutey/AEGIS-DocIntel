"""
aegis.intelligence.citations.support_evaluator
=============================================
Evaluates claim-level citation support across the 7-label canonical taxonomy:
SUPPORTS, PARTIALLY_SUPPORTS, CONTRADICTS, RELATED_ONLY, IRRELEVANT, INVALID_REFERENCE, INSUFFICIENT_CONTEXT.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set

from aegis.intelligence.citations.citation_resolver import CitationResolver
from aegis.intelligence.models import (
    CitationRef,
    CitationSummary,
    ClaimCitationEvaluation,
    ClaimItem,
    ClaimSupportStatus,
    SupportLabel,
)


class SupportEvaluator:
    """Classifies factual claim entailment and computes citation precision metrics."""

    def __init__(self, resolver: Optional[CitationResolver] = None):
        self.resolver = resolver or CitationResolver()

    @staticmethod
    def _extract_keywords(text: str) -> Set[str]:
        words = re.findall(r"\b[A-Za-z0-9_\-\$]+\b", text.lower())
        stopwords = {
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "or",
            "is", "was", "are", "were", "by", "from", "with", "as", "it", "that",
        }
        return {w for w in words if w not in stopwords and len(w) > 1}

    def evaluate_citation(
        self,
        claim_text: str,
        citation: CitationRef,
        evidence_text: Optional[str] = None,
    ) -> SupportLabel:
        """Evaluate a single citation reference against cited evidence text."""
        # 1. Structural / reference validity
        valid, reason = self.resolver.is_resolvable(citation)
        if not valid:
            return SupportLabel.INVALID_REFERENCE

        ev_text = (evidence_text or "").strip()
        if not ev_text:
            return SupportLabel.INSUFFICIENT_CONTEXT

        c_words = self._extract_keywords(claim_text)
        e_words = self._extract_keywords(ev_text)

        if not c_words or not e_words:
            return SupportLabel.INSUFFICIENT_CONTEXT

        # 2. Check for explicit contradictions
        c_lower = claim_text.lower()
        e_lower = ev_text.lower()

        # Check directional contradictions
        if ("increase" in c_lower and ("decrease" in e_lower or "decline" in e_lower)) or (
            "decrease" in c_lower and ("increase" in e_lower or "grow" in e_lower)
        ):
            return SupportLabel.CONTRADICTS

        # Check numeric mismatches on same attribute
        c_nums = set(re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", claim_text))
        e_nums = set(re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", ev_text))
        if c_nums and e_nums and not c_nums.intersection(e_nums):
            # Same topic keywords present but different numbers
            topic_overlap = c_words.intersection(e_words) - c_nums
            if len(topic_overlap) >= 2:
                return SupportLabel.CONTRADICTS

        # 3. Calculate keyword overlap
        overlap = c_words.intersection(e_words)
        overlap_ratio = len(overlap) / len(c_words)

        if overlap_ratio >= 0.70:
            # If numbers exist in claim, they must be grounded
            if c_nums and not c_nums.issubset(e_nums):
                return SupportLabel.PARTIALLY_SUPPORTS
            return SupportLabel.SUPPORTS
        elif overlap_ratio >= 0.35:
            return SupportLabel.PARTIALLY_SUPPORTS
        elif overlap_ratio > 0.10:
            return SupportLabel.RELATED_ONLY
        else:
            return SupportLabel.IRRELEVANT

    def evaluate_answer(
        self,
        answer_id: str,
        answer_text: str,
        claims: List[ClaimItem],
        evidence_store: Dict[str, str],  # mapping citation_id or chunk_id -> evidence_text
        question_id: Optional[str] = None,
    ) -> ClaimCitationEvaluation:
        """Evaluate all claims and citations within an answer."""
        evaluated_claims: List[ClaimItem] = []
        total_citations = 0
        supporting_citations = 0

        for claim in claims:
            evaluated_citations: List[CitationRef] = []
            claim_has_support = False
            claim_has_partial = False
            claim_has_contradiction = False

            for cit in claim.citations:
                total_citations += 1
                ev_text = (
                    evidence_store.get(cit.citation_id)
                    or evidence_store.get(cit.chunk_id or "")
                    or evidence_store.get(cit.document_id, "")
                )
                lbl = self.evaluate_citation(claim_text=claim.text, citation=cit, evidence_text=ev_text)

                evaluated_cit = CitationRef(
                    citation_id=cit.citation_id,
                    document_id=cit.document_id,
                    page_number=cit.page_number,
                    region_id=cit.region_id,
                    chunk_id=cit.chunk_id,
                    support_label=lbl,
                    confidence=1.0 if lbl == SupportLabel.SUPPORTS else 0.5,
                )
                evaluated_citations.append(evaluated_cit)

                if lbl == SupportLabel.SUPPORTS:
                    supporting_citations += 1
                    claim_has_support = True
                elif lbl == SupportLabel.PARTIALLY_SUPPORTS:
                    claim_has_partial = True
                elif lbl == SupportLabel.CONTRADICTS:
                    claim_has_contradiction = True

            # Determine claim status
            if claim_has_contradiction:
                status = ClaimSupportStatus.CONTRADICTED
            elif claim_has_support:
                status = ClaimSupportStatus.FULLY_SUPPORTED
            elif claim_has_partial:
                status = ClaimSupportStatus.PARTIALLY_SUPPORTED
            else:
                status = ClaimSupportStatus.UNSUPPORTED

            evaluated_claims.append(
                ClaimItem(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    citations=evaluated_citations,
                    support_status=status,
                )
            )

        n_claims = len(evaluated_claims)
        supported_claims = sum(1 for c in evaluated_claims if c.support_status == ClaimSupportStatus.FULLY_SUPPORTED)
        claims_with_citations = sum(1 for c in evaluated_claims if len(c.citations) > 0)

        cit_prec = (supporting_citations / total_citations) if total_citations > 0 else 0.0
        claim_supp = (supported_claims / n_claims) if n_claims > 0 else 0.0
        cit_cov = (claims_with_citations / n_claims) if n_claims > 0 else 0.0
        unsupp_rate = ((n_claims - supported_claims) / n_claims) if n_claims > 0 else 0.0

        summary = CitationSummary(
            citation_precision=round(cit_prec, 4),
            claim_support_rate=round(claim_supp, 4),
            citation_coverage=round(cit_cov, 4),
            unsupported_claim_rate=round(unsupp_rate, 4),
            total_claims=n_claims,
            total_citations=total_citations,
        )

        return ClaimCitationEvaluation(
            answer_id=answer_id,
            question_id=question_id,
            answer_text=answer_text,
            claims=evaluated_claims,
            evaluation_summary=summary,
        )
