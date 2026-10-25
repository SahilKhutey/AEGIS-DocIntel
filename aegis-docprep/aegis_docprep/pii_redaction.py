'''
aegis-docprep — PII & Compliance Redaction Module
=================================================
Scans extracted document elements for sensitive PII and regulated data (SSNs, credit cards, phone numbers, person names).
Applies redaction, tokenization, or flagging policies before downstream engines or external LLMs execute.
'''
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union


class PIIRedactionPolicyError(RuntimeError):
    """Raised when mandatory redaction fails or privacy validation policy is violated."""
    pass


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
    def safe_summary(self) -> Dict[str, Any]:
        """Returns safe aggregate telemetry without sensitive matched strings."""
        by_category: Dict[str, int] = {}
        for ent in self.entities_found:
            by_category[ent.entity_type] = by_category.get(ent.entity_type, 0) + 1
        return {
            "document_id": self.document_id,
            "total_entities_found": len(self.entities_found),
            "redactions_applied": self.redactions_applied,
            "entity_categories": by_category,
            "policy_version": self.policy_version,
        }


# Structured PII Regex Patterns with Validation Logic
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
PHONE_REGEX = re.compile(
    r'(?:(?<!\w)\+\d{1,4}[-\s]?(?:\(\d{1,4}\)[-\s]?)?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,9}\b)|'
    r'(?:\b(?:\+?1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b)|'
    r'(?:(?<![\d-])\b\d{3}-\d{4}\b)'
)
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
API_KEY_REGEX = re.compile(r'\b(?:sk-[a-zA-Z0-9_\-]{20,}|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{30,}|github_pat_[0-9a-zA-Z_]{22,})\b')

NON_NAME_WORDS = {
    "Contact", "Visited", "Invoice", "Ref", "Document", "Section", "Table", "Figure",
    "Report", "Annual", "Executive", "Summary", "Total", "Net", "Gross", "Revenue",
    "Margin", "Operating", "Financial", "System", "Service", "Engine", "Member", "Card",
    "Order", "ID", "Number", "Date", "Status", "Type", "Format", "Page", "Block", "Pay",
    "Call", "Customer", "Client", "Patient", "User", "Account", "Dear", "Agent", "Manager",
    "Employee", "Developer", "Director", "Managing", "Executive", "Senior", "Chief", "Officer", "Lead", "Head", "President", "Vice", "Author", "Sender", "Recipient", "Dr", "Mr", "Mrs", "Ms", "Prof",
}

# Exclusion lists for Title Case pairs that are locations
GEO_EXCLUSIONS = {
    "New York", "Hong Kong", "United States", "San Francisco", "Los Angeles",
    "North America", "South America", "Great Britain", "New Zealand", "Puerto Rico",
    "Saudi Arabia", "South Africa", "Sri Lanka", "Costa Rica", "El Salvador",
}

TITLE_CASE_RUN = re.compile(r'\b[A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20})+\b')
WORD_TOKEN = re.compile(r'[A-Z][a-z]{1,20}')


def _luhn_check(card_num: str) -> bool:
    """Verifies Luhn mod-10 checksum for credit card numbers."""
    digits = [int(c) for c in card_num if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            double = digit * 2
            checksum += double - 9 if double > 9 else double
        else:
            checksum += digit
    return checksum % 10 == 0


def detect_pii(element: Union[Dict[str, Any], str]) -> List[PIIEntity]:
    '''
    Detects structured and unstructured PII in an element text span or raw string.
    '''
    if isinstance(element, str):
        text = element
        elem_id = "elem_0"
    else:
        text = str(element.get('text', element.get('content', '')))
        elem_id = str(element.get('id', 'elem_0'))

    entities: List[PIIEntity] = []

    def _is_overlapping(s: int, e: int) -> bool:
        return any(ent.start < e and s < ent.end for ent in entities)

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
        match_text = match.group(0)
        score = 0.95 if _luhn_check(match_text) else 0.55
        if not _is_overlapping(match.start(), match.end()):
            entities.append(
                PIIEntity(
                    entity_type='CREDIT_CARD',
                    element_id=elem_id,
                    start=match.start(),
                    end=match.end(),
                    score=score,
                    text=match_text,
                )
            )

    for match in EMAIL_REGEX.finditer(text):
        if not _is_overlapping(match.start(), match.end()):
            entities.append(
                PIIEntity(
                    entity_type='EMAIL',
                    element_id=elem_id,
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                    text=match.group(0),
                )
            )

    for match in API_KEY_REGEX.finditer(text):
        if not _is_overlapping(match.start(), match.end()):
            entities.append(
                PIIEntity(
                    entity_type='API_KEY',
                    element_id=elem_id,
                    start=match.start(),
                    end=match.end(),
                    score=0.99,
                    text=match.group(0),
                )
            )

    for match in PHONE_REGEX.finditer(text):
        if not _is_overlapping(match.start(), match.end()):
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

    for match in TITLE_CASE_RUN.finditer(text):
        full_span = match.group(0)
        tokens = list(WORD_TOKEN.finditer(full_span))
        start_idx = 0
        while start_idx < len(tokens) and tokens[start_idx].group(0) in NON_NAME_WORDS:
            start_idx += 1
        end_idx = len(tokens)
        while end_idx > start_idx and tokens[end_idx - 1].group(0) in NON_NAME_WORDS:
            end_idx -= 1

        valid_tokens = tokens[start_idx:end_idx]
        if len(valid_tokens) >= 2:
            name_text = full_span[valid_tokens[0].start():valid_tokens[-1].end()]
            words = name_text.split()
            if (
                name_text not in GEO_EXCLUSIONS
                and not any(w in NON_NAME_WORDS for w in words)
            ):
                abs_start = match.start() + valid_tokens[0].start()
                abs_end = match.start() + valid_tokens[-1].end()
                if not _is_overlapping(abs_start, abs_end):
                    entities.append(
                        PIIEntity(
                            entity_type='PERSON',
                            element_id=elem_id,
                            start=abs_start,
                            end=abs_end,
                            score=0.85,
                            text=name_text,
                        )
                    )

    return entities


def apply_redaction_policy(
    element: Union[Dict[str, Any], str],
    entities: List[PIIEntity],
    policies: Optional[List[RedactionPolicy]] = None,
) -> Union[Tuple[Dict[str, Any], ComplianceReport], str]:
    '''
    Applies redaction, tokenization, or flagging per policy configuration.
    
    If element is a dictionary, returns a tuple: (redacted_element_dict, compliance_report).
    If element is a string, returns the redacted string directly.
    '''
    default_policies = policies or [
        RedactionPolicy('US_SSN', 'redact'),
        RedactionPolicy('CREDIT_CARD', 'redact'),
        RedactionPolicy('PHONE_NUMBER', 'redact'),
        RedactionPolicy('PERSON', 'redact'),
        RedactionPolicy('EMAIL', 'redact'),
        RedactionPolicy('API_KEY', 'redact'),
    ]
    policy_map = {p.entity_type: p for p in default_policies}

    if isinstance(element, str):
        text = element
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
        for ent in sorted_entities:
            pol = policy_map.get(ent.entity_type, RedactionPolicy(ent.entity_type, 'redact'))
            if pol.action == 'redact':
                rep = pol.replacement or f"<{ent.entity_type}_REDACTED>"
                text = text[: ent.start] + rep + text[ent.end :]
            elif pol.action == 'tokenize':
                token_hash = hashlib.sha256(ent.text.encode('utf-8')).hexdigest()[:4].upper()
                rep = pol.replacement or f"<TOK_{token_hash}>"
                text = text[: ent.start] + rep + text[ent.end :]
        return text

    elem_copy = dict(element)
    text_key = 'text' if 'text' in elem_copy else ('content' if 'content' in elem_copy else 'text')
    text = str(elem_copy.get(text_key, ''))
    doc_id = str(element.get('doc_id', 'doc_0'))

    redaction_count = 0
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

    for ent in sorted_entities:
        pol = policy_map.get(ent.entity_type, RedactionPolicy(ent.entity_type, 'redact'))

        if pol.action == 'redact':
            rep = pol.replacement or f"<{ent.entity_type}_REDACTED>"
            text = text[: ent.start] + rep + text[ent.end :]
            redaction_count += 1
        elif pol.action == 'tokenize':
            token_hash = hashlib.sha256(ent.text.encode('utf-8')).hexdigest()[:4].upper()
            rep = pol.replacement or f"<TOK_{token_hash}>"
            text = text[: ent.start] + rep + text[ent.end :]
            redaction_count += 1
        elif pol.action == 'flag_only':
            elem_copy['has_pii_flag'] = True

    elem_copy['text'] = text
    if 'content' in elem_copy:
        elem_copy['content'] = text
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
    Scans and redacts a list of document element objects or dictionaries.
    Returns (redacted_elements, aggregate_compliance_report).
    '''
    default_policies = policies or [
        RedactionPolicy('US_SSN', 'redact'),
        RedactionPolicy('CREDIT_CARD', 'redact'),
        RedactionPolicy('PHONE_NUMBER', 'redact'),
        RedactionPolicy('EMAIL_ADDRESS', 'redact'),
        RedactionPolicy('API_KEY_TOKEN', 'redact'),
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



def redact_or_block(
    content: Any,
    policies: Optional[List[RedactionPolicy]] = None,
    mandatory: bool = True,
) -> Tuple[Any, ComplianceReport]:
    """
    Applies PII redaction according to policy with fail-closed safety.
    If mandatory=True and an unexpected error occurs, raises PIIRedactionPolicyError,
    blocking downstream external transfer rather than leaking plaintext data.
    """
    default_p = policies or [
        RedactionPolicy('US_SSN', 'redact'),
        RedactionPolicy('CREDIT_CARD', 'redact'),
        RedactionPolicy('PHONE_NUMBER', 'redact'),
        RedactionPolicy('EMAIL', 'redact'),
        RedactionPolicy('API_KEY', 'redact'),
        RedactionPolicy('PERSON', 'redact'),
    ]
    try:
        if isinstance(content, str):
            entities = detect_pii(content)
            redacted_text = apply_redaction_policy(content, entities, default_p)
            report = ComplianceReport(
                document_id="doc_str",
                entities_found=entities,
                redactions_applied=len(entities),
            )
            return redacted_text, report
        elif isinstance(content, list):
            return redact_elements(content, default_p)
        else:
            entities = detect_pii(content)
            res = apply_redaction_policy(content, entities, default_p)
            if isinstance(res, tuple):
                return res
            report = ComplianceReport(
                document_id="doc_elem",
                entities_found=entities,
                redactions_applied=len(entities),
            )
            return res, report
    except Exception as exc:
        if mandatory:
            raise PIIRedactionPolicyError(f"Mandatory redaction failed: {exc}") from exc
        raise
