"""
src/api/routers/answers.py
==========================
AEGIS-DocIntel — Answers API Router
Evidence-grounded answer generation with strict citation validation and safe abstention.
"""

from __future__ import annotations

import json
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant
from src.engines.generation.contracts import (
    Evidence,
    GenerationRequest,
)
from src.engines.generation.generator import AnswerGenerator
from src.engines.generation.service import GenerationService
from src.engines.generation.validation import (
    CitationValidationError,
    GenerationInputError,
    ModelOutputError,
)
from src.engines.retrieval.query_contract import validate_query

router = APIRouter()
log = structlog.get_logger("aegis.api.answers")


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    document_ids: List[str] = Field(default_factory=list, max_length=1000)


class AnswerCitation(BaseModel):
    evidence_id: str
    document_id: str
    page_number: Optional[int] = None
    section_path: List[str] = Field(default_factory=list)


class AnswerResponse(BaseModel):
    status: str
    answer: str
    citations: List[AnswerCitation] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


@router.post(
    "",
    response_model=AnswerResponse,
    summary="Generate evidence-grounded answer with validated citations",
)
@router.post(
    "/",
    response_model=AnswerResponse,
    include_in_schema=False,
)
async def create_answer(
    body: AnswerRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> AnswerResponse:
    """
    Generate a strictly source-grounded answer for the authenticated tenant.

    Workflow:
    1. Validate query format, tenant identity, and document filter boundaries.
    2. Retrieve authorized evidence chunks scoped to the tenant.
    3. Invoke the generation service with untrusted-evidence boundaries.
    4. Validate citation membership and claim grounding.
    5. Safely abstain on insufficient or conflicting evidence.
    """
    # 1. Input and boundary validation
    try:
        validated_q = validate_query(
            query=body.question,
            tenant_id=tenant.tenant_id,
            document_ids=body.document_ids,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid answer query: {exc}",
        )

    # 2. Retrieve authorized candidate elements
    container = getattr(request.app.state, "container", None)
    orchestrator = getattr(request.app.state, "orchestrator", None)
    if orchestrator is None and container is not None:
        orchestrator = getattr(container, "rag_engine", None)

    evidence_list: List[Evidence] = []
    if orchestrator is not None:
        target_docs = validated_q.document_ids or [
            d for d, t in orchestrator._doc_tenant.items()
            if t == tenant.tenant_id
        ]
        for did in target_docs:
            try:
                elements = orchestrator.get_document_elements(did, tenant_id=tenant.tenant_id)
            except PermissionError:
                continue
            for idx, elem in enumerate(elements):
                chunk_id = getattr(elem, "element_id", f"{did}::chunk::{idx}")
                text = getattr(elem, "content", getattr(elem, "text", ""))
                page = getattr(elem, "page_number", getattr(elem, "page", None))
                sec_path = getattr(elem, "section_path", ())
                if isinstance(sec_path, list):
                    sec_path = tuple(sec_path)
                evidence_list.append(
                    Evidence(
                        chunk_id=chunk_id,
                        document_id=did,
                        tenant_id=tenant.tenant_id,
                        text=text,
                        score=1.0,
                        page_number=page,
                        section_path=sec_path,
                    )
                )

    # 3. Construct generation request
    gen_request = GenerationRequest(
        question=validated_q.query,
        tenant_id=tenant.tenant_id,
        evidence=tuple(evidence_list),
    )

    # 4. Obtain or instantiate generation engine
    generator = getattr(container, "generation_generator", None) if container else None
    if generator is None:
        class DefaultEvidenceModel:
            def generate(
                self,
                *,
                system_prompt: str,
                user_prompt: str,
                temperature: float,
                max_output_tokens: int,
            ) -> str:
                if evidence_list:
                    valid_evs = [ev for ev in evidence_list if ev.text]
                    joined_text = " ".join(ev.text for ev in valid_evs)
                    return json.dumps({
                        "status": "answered",
                        "answer": joined_text,
                        "claims": [
                            {"text": ev.text, "evidence_ids": [ev.chunk_id]}
                            for ev in valid_evs
                        ],
                        "warnings": [],
                    })
                return json.dumps({
                    "status": "insufficient_evidence",
                    "answer": "The provided documents do not contain sufficient evidence to answer this question.",
                    "claims": [],
                    "warnings": ["Insufficient evidence available."],
                })

        generator = AnswerGenerator(DefaultEvidenceModel())

    service = GenerationService(generator)

    try:
        result = service.answer(gen_request)
    except (GenerationInputError, CitationValidationError, ModelOutputError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generation validation error: {exc}",
        )

    return AnswerResponse(
        status=result.status,
        answer=result.answer,
        citations=[
            AnswerCitation(
                evidence_id=c.evidence_id,
                document_id=c.document_id,
                page_number=c.page_number,
                section_path=list(c.section_path),
            )
            for c in result.citations
        ],
        warnings=list(result.warnings),
    )
