"""
src/engines/generation/validation.py
====================================
Deterministic validation for generation requests, model outputs, and citation integrity.
"""

from __future__ import annotations

import json
from typing import Dict, List, Set, Tuple

from .contracts import (
    Citation,
    Claim,
    Evidence,
    GenerationPolicy,
    GenerationRequest,
    GenerationResult,
)


class GenerationError(Exception):
    """Base exception for all generation pipeline errors."""


class GenerationInputError(GenerationError, ValueError):
    """The generation request is malformed or exceeds configured limits."""


class CitationValidationError(GenerationError, ValueError):
    """The generated answer refers to evidence it was not given or that is unauthorized."""


class ModelOutputError(GenerationError, ValueError):
    """The model response does not satisfy the required schema or constraints."""


ALLOWED_STATUSES = {
    "answered",
    "insufficient_evidence",
    "conflicting_evidence",
}


def validate_generation_request(
    request: GenerationRequest,
    policy: GenerationPolicy,
) -> None:
    """Validate request boundaries, payload limits, and tenant ownership before generation."""
    if not isinstance(request.question, str) or not request.question.strip():
        raise GenerationInputError("question must not be empty")

    if len(request.question) > policy.max_question_chars:
        raise GenerationInputError(
            f"question exceeds maximum length of {policy.max_question_chars} characters"
        )

    if not isinstance(request.tenant_id, str) or not request.tenant_id.strip():
        raise GenerationInputError("tenant_id must not be empty")

    if not isinstance(request.evidence, (tuple, list)):
        raise GenerationInputError("evidence must be a tuple or list of Evidence objects")

    if len(request.evidence) > policy.max_evidence_items:
        raise GenerationInputError(
            f"evidence count ({len(request.evidence)}) exceeds maximum limit of {policy.max_evidence_items}"
        )

    # Strictly enforce tenant isolation across all supplied evidence
    normalized_tenant = request.tenant_id.strip()
    for ev in request.evidence:
        if not isinstance(ev, Evidence):
            raise GenerationInputError("All items in evidence must be Evidence instances")
        if ev.tenant_id.strip() != normalized_tenant:
            raise GenerationInputError(
                f"Evidence '{ev.chunk_id}' belongs to tenant '{ev.tenant_id}', unauthorized for request tenant '{normalized_tenant}'"
            )


def parse_model_output(raw: str) -> GenerationResult:
    """Parse raw model output into a preliminary GenerationResult, validating the JSON schema."""
    if not isinstance(raw, str):
        raise ModelOutputError("model output must be a string")

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ModelOutputError(f"model output is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ModelOutputError("model output must be a JSON object")

    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        raise ModelOutputError(
            f"invalid generation status '{status}'; expected one of {sorted(ALLOWED_STATUSES)}"
        )

    answer = data.get("answer")
    if not isinstance(answer, str):
        raise ModelOutputError("model output must contain a string 'answer' field")

    raw_claims = data.get("claims", [])
    if not isinstance(raw_claims, list):
        raise ModelOutputError("'claims' field must be a list")

    parsed_claims: List[Claim] = []
    for idx, c in enumerate(raw_claims):
        if not isinstance(c, dict):
            raise ModelOutputError(f"claim [{idx}] must be a JSON object")
        c_text = c.get("text")
        if not isinstance(c_text, str) or not c_text.strip():
            raise ModelOutputError(f"claim [{idx}] has invalid or empty 'text'")
        e_ids = c.get("evidence_ids", [])
        if not isinstance(e_ids, (list, tuple)):
            raise ModelOutputError(f"claim [{idx}] 'evidence_ids' must be a list")
        parsed_claims.append(
            Claim(
                text=c_text.strip(),
                evidence_ids=tuple(str(eid).strip() for eid in e_ids if str(eid).strip()),
            )
        )

    raw_warnings = data.get("warnings", [])
    if not isinstance(raw_warnings, list):
        raw_warnings = []
    warnings = tuple(str(w) for w in raw_warnings)

    return GenerationResult(
        status=status,
        answer=answer,
        claims=tuple(parsed_claims),
        citations=(),
        warnings=warnings,
    )


def validate_claim_references(
    result: GenerationResult,
    evidence: Tuple[Evidence, ...],
) -> None:
    """Ensure all claims in an answered result cite supplied, authorized evidence items."""
    evidence_by_id: Dict[str, Evidence] = {item.chunk_id: item for item in evidence}

    if result.status == "answered":
        if not result.claims:
            raise CitationValidationError("answered response must contain at least one claim")

        for claim in result.claims:
            if not claim.evidence_ids:
                raise CitationValidationError(
                    f"factual claim '{claim.text}' has no evidence reference"
                )
            for evidence_id in claim.evidence_ids:
                if evidence_id not in evidence_by_id:
                    raise CitationValidationError(
                        f"claim references unknown evidence: {evidence_id}"
                    )


def resolve_citations(
    result: GenerationResult,
    evidence: Tuple[Evidence, ...],
) -> Tuple[Citation, ...]:
    """Map validated claim evidence references to canonical Citation metadata."""
    evidence_by_id: Dict[str, Evidence] = {item.chunk_id: item for item in evidence}
    seen_ids: Set[str] = set()
    citations: List[Citation] = []

    for claim in result.claims:
        for eid in claim.evidence_ids:
            if eid in evidence_by_id and eid not in seen_ids:
                seen_ids.add(eid)
                ev = evidence_by_id[eid]
                citations.append(
                    Citation(
                        evidence_id=ev.chunk_id,
                        document_id=ev.document_id,
                        page_number=ev.page_number,
                        section_path=ev.section_path,
                    )
                )

    return tuple(citations)
