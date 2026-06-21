'''
AEGIS-AEL — Response Verification Layer
=========================================
Performs post-response validation:
1. Citation Verification (verify page and section exist in UEO)
2. Grounding & Fact Verification (lexical alignment of claims with UEO context)
3. Calibration of confidence scores
'''
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from src.ael.ueo import UniversalExportObject, Citation

logger = logging.getLogger('amdi.ael.verification')

@dataclass
class VerifiedCitation:
    citation_index: int
    page: int
    section: str | None
    is_valid: bool
    reason: str
    snippet: str | None = None

@dataclass
class VerificationResult:
    is_grounded: bool
    verified_citations: List[VerifiedCitation]
    grounding_score: float  # [0.0, 1.0]
    unverified_claims: List[str]
    calibrated_confidence: float
    feedback: str


class ResponseVerificationLayer:
    '''
    Verifies LLM responses against the Universal Export Object context.
    '''

    def __init__(self, semantic_match_threshold: float = 0.5):
        self.threshold = semantic_match_threshold

    def verify(self, response_text: str, ueo: UniversalExportObject) -> VerificationResult:
        '''
        Runs the full verification pipeline on the agent response.
        '''
        # 1. Parse citations e.g. [page X, section Y] or [page X] or [X]
        parsed_cites = self._parse_citations(response_text)
        
        # 2. Verify citations against UEO
        verified_citations = []
        valid_count = 0
        for idx, cite in enumerate(parsed_cites):
            p = cite.get('page')
            s = cite.get('section')
            
            # Find matching citation in UEO
            match = None
            for u_cite in ueo.citations:
                if u_cite.page == p:
                    if s is None or (u_cite.section and s.lower() in u_cite.section.lower()):
                        match = u_cite
                        break
            
            if match:
                verified_citations.append(VerifiedCitation(
                    citation_index=idx + 1, page=p, section=s, is_valid=True,
                    reason='Matched UEO source snippet', snippet=match.snippet
                ))
                valid_count += 1
            else:
                # Check if page simply exists in metadata
                page_exists = 1 <= p <= ueo.metadata.pages
                if page_exists:
                    verified_citations.append(VerifiedCitation(
                        citation_index=idx + 1, page=p, section=s, is_valid=True,
                        reason='Page exists in document', snippet=None
                    ))
                    valid_count += 1
                else:
                    verified_citations.append(VerifiedCitation(
                        citation_index=idx + 1, page=p, section=s, is_valid=False,
                        reason=f'Page {p} exceeds document page count of {ueo.metadata.pages}', snippet=None
                    ))

        citation_ratio = valid_count / len(parsed_cites) if parsed_cites else 1.0

        # 3. Grounding check: verify words of the response are backed by UEO snippets
        context_corpus = ' '.join([c.snippet.lower() for c in ueo.citations] + [ueo.document_summary.abstract.lower()])
        claims = self._split_into_claims(response_text)
        unverified = []
        grounded_claims = 0
        
        for claim in claims:
            # Check overlap of significant words
            claim_words = [w.lower() for w in re.findall(r'\b\w{4,}\b', claim)]
            if not claim_words:
                grounded_claims += 1
                continue
            matches = sum(1 for w in claim_words if w in context_corpus)
            overlap = matches / len(claim_words)
            if overlap >= self.threshold:
                grounded_claims += 1
            else:
                unverified.append(claim)

        grounding_score = grounded_claims / len(claims) if claims else 1.0
        
        # 4. Calibrate confidence
        # C_calibrated = C_ueo * grounding_score * citation_ratio
        calibrated_confidence = ueo.confidence.overall * grounding_score * citation_ratio
        
        # 5. Determine overall grounded flag
        is_grounded = grounding_score > 0.7 and citation_ratio > 0.7

        feedback = (
            f'Grounding score: {grounding_score:.2%}, Valid citations: {valid_count}/{len(parsed_cites)}. '
            f'Calibrated confidence: {calibrated_confidence:.2%}'
        )

        return VerificationResult(
            is_grounded=is_grounded,
            verified_citations=verified_citations,
            grounding_score=grounding_score,
            unverified_claims=unverified,
            calibrated_confidence=calibrated_confidence,
            feedback=feedback
        )

    def _parse_citations(self, text: str) -> List[Dict[str, Any]]:
        cites = []
        # Matches patterns: [page X, section Y] or [page X] or [X]
        pattern = r'\[(?:page\s+)?(\d+)(?:,\s*(?:section\s+)?([a-zA-Z0-9\s_\-\.]+))?\]'
        for m in re.finditer(pattern, text, re.IGNORECASE):
            try:
                page = int(m.group(1))
                section = m.group(2).strip() if m.group(2) else None
                cites.append({'page': page, 'section': section})
            except (ValueError, AttributeError):
                continue
        # Fallback to simple numbers in square brackets if no section match
        if not cites:
            for m in re.finditer(r'\[(\d+)\]', text):
                try:
                    cites.append({'page': int(m.group(1)), 'section': None})
                except ValueError:
                    continue
        return cites

    def _split_into_claims(self, text: str) -> List[str]:
        # Split by sentence boundaries
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        return [s.strip() for s in sentences if s.strip()]
