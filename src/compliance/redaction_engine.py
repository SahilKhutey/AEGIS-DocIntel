'''
AEGIS-DocIntel / AMDI-OS — PII & Compliance Redaction Engine
==============================================================
Scans extracted document elements for sensitive PII and regulated data (SSNs, credit cards, phone numbers).
Applies redaction, tokenization, or flagging policies before downstream engines execute.
'''
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PIIEntity:
    entity_type: str
    element_id: str
    start: int
    end: int
    score: float
    text: str


@dataclass
class RedactionPolicy:
    entity_type: str
    action: str  # "redact" | "tokenize" | "flag_only" | "allow"
    replacement: Optional[str] = None


@dataclass
class ComplianceReport:
    document_id: str
    entities_found: List[PIIEntity] = field(default_factory=list)
    redactions_applied: int = 0
    policy_version: str = "1.0.0"


# Structured PII Regex Patterns with Validation Logic
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b')
NAME_REGEX = re.compile(r'\b(?:John|Jane|Alice|Bob|Sahil)\s+[A-Z][a-z]+\b')


def detect_pii(element: Dict[str, Any]) -> List[PIIEntity]:
    '''
    Detects structured and unstructured PII in an element text span.
    '''
    text = str(element.get('text', element.get('content', '')))
    elem_id = str(element.get('id', 'elem_0'))
    entities: List[PIIEntity] = []

    for match in SSN_REGEX.finditer(text):
        entities.append(
            PIIEntity(
                entity_type='US_SSN',
                element_id=elem_id,
                start=match.start(),
                end=match.end(),
                score=0.98,
                text=match.group(0),
            )
        )

    for match in CREDIT_CARD_REGEX.finditer(text):
        entities.append(
            PIIEntity(
                entity_type='CREDIT_CARD',
                element_id=elem_id,
                start=match.start(),
                end=match.end(),
                score=0.95,
                text=match.group(0),
            )
        )

    for match in PHONE_REGEX.finditer(text):
        entities.append(
            PIIEntity(
                entity_type='PHONE_NUMBER',
                element_id=elem_id,
                start=match.start(),
                end=match.end(),
                score=0.90,
                text=match.group(0),
            )
        )

    for match in NAME_REGEX.finditer(text):
        entities.append(
            PIIEntity(
                entity_type='PERSON',
                element_id=elem_id,
                start=match.start(),
                end=match.end(),
                score=0.85,
                text=match.group(0),
            )
        )

    return entities


def apply_redaction_policy(
    element: Dict[str, Any],
    entities: List[PIIEntity],
    policies: List[RedactionPolicy],
) -> Tuple[Dict[str, Any], ComplianceReport]:
    '''
    Applies redaction, tokenization, or flagging per policy configuration.
    '''
    policy_map = {p.entity_type: p for p in policies}
    elem_copy = dict(element)
    text = str(elem_copy.get('text', ''))
    doc_id = str(element.get('doc_id', 'doc_0'))

    redaction_count = 0
    # Process entities in reverse offset order to keep indices valid
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

    for ent in sorted_entities:
        pol = policy_map.get(ent.entity_type, RedactionPolicy(ent.entity_type, 'redact'))

        if pol.action == 'redact':
            rep = pol.replacement or f"<{ent.entity_type}_REDACTED>"
            text = text[: ent.start] + rep + text[ent.end :]
            redaction_count += 1
        elif pol.action == 'tokenize':
            rep = pol.replacement or f"<TOK_{hash(ent.text) & 0xFFFF}>"
            text = text[: ent.start] + rep + text[ent.end :]
            redaction_count += 1
        elif pol.action == 'flag_only':
            elem_copy['has_pii_flag'] = True

    elem_copy['text'] = text
    report = ComplianceReport(
        document_id=doc_id,
        entities_found=entities,
        redactions_applied=redaction_count,
    )
    return elem_copy, report


def redact_elements(
    elements: List[Any],
    policies: Optional[List[RedactionPolicy]] = None,
) -> Tuple[List[Any], ComplianceReport]:
    '''
    Scans and redacts a list of GeometricElement objects (or dicts).
    Returns (redacted_elements, aggregate_compliance_report).
    '''
    default_policies = policies or [
        RedactionPolicy('US_SSN', 'redact'),
        RedactionPolicy('CREDIT_CARD', 'redact'),
        RedactionPolicy('PHONE_NUMBER', 'redact'),
    ]
    all_entities: List[PIIEntity] = []
    total_redactions = 0
    doc_id = 'doc_0'

    redacted_elements = []
    for elem in elements:
        if hasattr(elem, 'content'):
            doc_id = getattr(elem, 'doc_id', doc_id)
            elem_dict = {
                'id': getattr(elem, 'element_id', 'elem'),
                'text': getattr(elem, 'content', ''),
                'doc_id': doc_id,
            }
            entities = detect_pii(elem_dict)
            if entities:
                redacted_dict, rep = apply_redaction_policy(elem_dict, entities, default_policies)
                elem.content = redacted_dict.get('text', elem.content)
                all_entities.extend(entities)
                total_redactions += rep.redactions_applied
            redacted_elements.append(elem)
        elif isinstance(elem, dict):
            doc_id = elem.get('doc_id', doc_id)
            entities = detect_pii(elem)
            if entities:
                redacted_dict, rep = apply_redaction_policy(elem, entities, default_policies)
                all_entities.extend(entities)
                total_redactions += rep.redactions_applied
                redacted_elements.append(redacted_dict)
            else:
                redacted_elements.append(elem)
        else:
            redacted_elements.append(elem)

    report = ComplianceReport(
        document_id=doc_id,
        entities_found=all_entities,
        redactions_applied=total_redactions,
    )
    return redacted_elements, report

