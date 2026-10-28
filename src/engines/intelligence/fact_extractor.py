"""
src/engines/intelligence/fact_extractor.py
==========================================
Schema-guided structured fact extraction with exact evidence span verification
and untrusted document boundary protection.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.engines.intelligence.contracts import (
    EvidenceSpan,
    ExtractionResult,
    ExtractionSchema,
    FieldDefinition,
    ExtractedFact,
)
from src.engines.intelligence.entity_resolution import normalize_entity_label
from src.engines.intelligence.normalization import (
    normalize_boolean,
    normalize_currency_amount,
    normalize_date,
    normalize_day_count,
    normalize_unit,
    parse_decimal,
)


def verify_quote_in_source(
    quote: str,
    source_text: str,
    start_offset: Optional[int] = None,
    end_offset: Optional[int] = None,
) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Verify that quoted_text is strictly grounded in the source text.
    If offsets are provided, validates that source_text[start:end] matches the quote.
    If offsets are missing or inaccurate, searches source_text for the quote and
    returns computed deterministic start/end offsets.
    """
    if not quote or not source_text:
        return False, None, None

    cleaned_quote = quote.strip()
    if not cleaned_quote:
        return False, None, None

    # 1. If offsets are supplied, check if source_text[start:end] contains quote
    if start_offset is not None and end_offset is not None:
        if 0 <= start_offset < end_offset <= len(source_text):
            sliced = source_text[start_offset:end_offset]
            if cleaned_quote in sliced or sliced.strip() == cleaned_quote:
                return True, start_offset, end_offset

    # 2. Look for exact substring match
    idx = source_text.find(cleaned_quote)
    if idx != -1:
        return True, idx, idx + len(cleaned_quote)

    # 3. Case-insensitive search fallback
    idx_lower = source_text.lower().find(cleaned_quote.lower())
    if idx_lower != -1:
        return True, idx_lower, idx_lower + len(cleaned_quote)

    # 4. Whitespace-collapsed search fallback
    pattern = re.escape(cleaned_quote)
    pattern = re.sub(r"\\\s+", r"\\s+", pattern)
    m = re.search(pattern, source_text, re.IGNORECASE)
    if m:
        return True, m.start(), m.end()

    return False, None, None


def build_untrusted_document_envelope(document_id: str, content: str) -> str:
    """
    Wrap untrusted document content inside a secured JSON boundary envelope
    to prevent prompt escape or format injection.
    """
    envelope = {
        "__security_boundary__": "UNTRUSTED_DOCUMENT_SOURCE",
        "document_id": document_id,
        "content_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "payload": content,
    }
    return json.dumps(envelope, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────
# Standard Built-in Schemas
# ─────────────────────────────────────────────────────────────────

FINANCIAL_METRICS_SCHEMA = ExtractionSchema(
    schema_name="financial_metrics",
    schema_version=1,
    target_subject="financial_report",
    description="Standard corporate financial statement metrics",
    fields=(
        FieldDefinition(
            name="Revenue",
            attribute="revenue",
            value_type="decimal",
            unit="USD",
            description="Total revenues, sales, or turnover",
            patterns=(
                r"(?i)(?:total\s+)?revenue[s]?\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
                r"(?i)total\s+sales\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("total_revenue", "sales", "turnover"),
        ),
        FieldDefinition(
            name="Net Income",
            attribute="net_income",
            value_type="decimal",
            unit="USD",
            description="Net income, net earnings, or net profit",
            patterns=(
                r"(?i)net\s+income\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
                r"(?i)net\s+profit\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("net_profit", "net_earnings"),
        ),
        FieldDefinition(
            name="Operating Expenses",
            attribute="operating_expenses",
            value_type="decimal",
            unit="USD",
            description="Total operating expenses (OpEx)",
            patterns=(
                r"(?i)operating\s+expenses\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
                r"(?i)opex\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("opex", "operating_costs"),
        ),
        FieldDefinition(
            name="EBITDA",
            attribute="ebitda",
            value_type="decimal",
            unit="USD",
            description="Earnings before interest, taxes, depreciation, and amortization",
            patterns=(
                r"(?i)\bebitda\b\s*(?:of|was|is|reached|were|totaled)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("adjusted_ebitda",),
        ),
        FieldDefinition(
            name="Gross Margin",
            attribute="gross_margin",
            value_type="decimal",
            unit="percent",
            description="Gross profit margin percentage",
            patterns=(
                r"(?i)gross\s+margin\s*(?:of|was|is|reached|were)?\s*[:=\-]?\s*([\d.,]+\s*%)",
            ),
            aliases=("gross_profit_margin",),
        ),
        FieldDefinition(
            name="Cash and Cash Equivalents",
            attribute="cash_and_equivalents",
            value_type="decimal",
            unit="USD",
            description="Cash and cash equivalents at period close",
            patterns=(
                r"(?i)cash\s+and\s+(?:cash\s+)?equivalents\s*(?:of|was|is|reached|closed\s+at|stood\s+at)?\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("cash", "cash_reserves"),
        ),
    ),
)

CONTRACT_TERMS_SCHEMA = ExtractionSchema(
    schema_name="contract_terms",
    schema_version=1,
    target_subject="agreement",
    description="Standard legal contract terms and conditions",
    fields=(
        FieldDefinition(
            name="Effective Date",
            attribute="effective_date",
            value_type="date",
            description="Agreement commencement or effective date",
            patterns=(
                r"(?i)effective\s+date\s*(?:is|of|shall\s+be)?\s*[:=\-]?\s*([a-zA-Z0-9,\/\s\-]+?)(?:\s+by\s+and\s+between|\.|\n|;|$)",
                r"(?i)commencing\s+on\s*([a-zA-Z0-9,\/\s\-]+?)(?:\.|\n|;|$)",
            ),
            aliases=("start_date", "commencement_date"),
        ),
        FieldDefinition(
            name="Termination Date",
            attribute="termination_date",
            value_type="date",
            description="Agreement expiration or end date",
            patterns=(
                r"(?i)termination\s+date\s*(?:is|of|shall\s+be)?\s*[:=\-]?\s*([a-zA-Z0-9,\/\s\-]+?)(?:\.|\n|;|$)",
                r"(?i)expires\s+on\s*([a-zA-Z0-9,\/\s\-]+?)(?:\.|\n|;|$)",
                r"(?i)expiration\s+date\s*[:=\-]?\s*([a-zA-Z0-9,\/\s\-]+?)(?:\.|\n|;|$)",
            ),
            aliases=("expiration_date", "end_date"),
        ),
        FieldDefinition(
            name="Governing Law",
            attribute="governing_law",
            value_type="string",
            description="Jurisdiction or state law governing the contract",
            patterns=(
                r"(?i)governed\s+by\s+(?:the\s+laws\s+of\s+)?(?:the\s+State\s+of\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+without|\.|\n|;|,)",
                r"(?i)laws\s+of\s+(?:the\s+State\s+of\s+)?([A-Z][a-zA-Z\s]+?)\s+shall\s+govern",
            ),
            aliases=("jurisdiction", "applicable_law"),
        ),
        FieldDefinition(
            name="Liability Cap",
            attribute="liability_cap",
            value_type="decimal",
            unit="USD",
            description="Aggregate maximum liability limit",
            patterns=(
                r"(?i)(?:total\s+)?(?:aggregate\s+)?liability\s+(?:shall\s+not\s+exceed|capped\s+at|is\s+limited\s+to|cap\s+of)\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
                r"(?i)limitation\s+of\s+liability\s*[:=\-]?\s*([$€£¥₹]?\s*[\d.,]+\s*(?:billion|million|k|bn|mn)?(?:\s*(?:USD|EUR|GBP|JPY|CAD|AUD|CHF|INR))?)",
            ),
            aliases=("aggregate_liability", "liability_limit"),
        ),
        FieldDefinition(
            name="Payment Terms",
            attribute="payment_terms",
            value_type="quantity",
            unit="days",
            description="Net payment duration period",
            patterns=(
                r"(?i)payment\s+terms\s*[:=\-]?\s*(?:net\s*)?(\d+\s*(?:calendar\s+days?|business\s+days?|days?))",
                r"(?i)payable\s+within\s*(\d+\s*(?:calendar\s+days?|business\s+days?|days?))",
                r"(?i)net\s*(\d+)(?:\s*days)?",
            ),
            aliases=("net_payment_days", "payment_duration"),
        ),
        FieldDefinition(
            name="Notice Period",
            attribute="notice_period",
            value_type="quantity",
            unit="days",
            description="Required advance written termination or change notice",
            patterns=(
                r"(?i)(?:written\s+)?notice\s+(?:of|period\s*(?:of|[:=\-]))?\s*(\d+\s*(?:calendar\s+days?|business\s+days?|days?))",
                r"(?i)notice\s+period\s*[:=\-]?\s*(\d+\s*(?:calendar\s+days?|business\s+days?|days?))",
            ),
            aliases=("termination_notice",),
        ),
        FieldDefinition(
            name="Indemnification",
            attribute="indemnification",
            value_type="boolean",
            description="Whether mutual or unilateral indemnification is required",
            patterns=(
                r"(?i)indemnif(?:y|ication)\s+is\s+(required|waived|provided|excluded)",
                r"(?i)(shall\s+indemnify|agrees\s+to\s+indemnify)",
            ),
            aliases=("indemnity_obligation",),
        ),
    ),
)

BUILTIN_SCHEMAS: Dict[str, ExtractionSchema] = {
    "financial_metrics": FINANCIAL_METRICS_SCHEMA,
    "contract_terms": CONTRACT_TERMS_SCHEMA,
}


class FactExtractor:
    """
    Extracts schema-guided facts from raw text or document chunks with strict evidence grounding.
    """

    def __init__(self, schemas: Optional[Dict[str, ExtractionSchema]] = None) -> None:
        self.schemas = dict(BUILTIN_SCHEMAS)
        if schemas:
            self.schemas.update(schemas)

    def register_schema(self, schema: ExtractionSchema) -> None:
        self.schemas[schema.schema_name] = schema

    def extract_from_chunk(
        self,
        tenant_id: str,
        document_id: str,
        chunk_id: str,
        content: str,
        schema: ExtractionSchema,
        page_number: Optional[int] = None,
        subject_override: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """Extract facts conforming to a schema from a single document chunk."""
        extracted: List[ExtractedFact] = []
        target_subject = subject_override or schema.target_subject

        for field_def in schema.fields:
            for pattern_str in field_def.patterns:
                for match in re.finditer(pattern_str, content):
                    raw_val = match.group(1).strip() if match.lastindex and match.lastindex >= 1 else match.group(0).strip()
                    # Capture surrounding sentence or line as quoted evidence
                    full_match_text = match.group(0).strip()
                    start_off = match.start()
                    end_off = match.end()

                    # Verify evidence span grounding
                    valid_quote, s_off, e_off = verify_quote_in_source(
                        quote=full_match_text,
                        source_text=content,
                        start_offset=start_off,
                        end_offset=end_off,
                    )
                    if not valid_quote:
                        continue

                    # Parse typed value
                    parsed_val: Any = raw_val
                    unit = field_def.unit

                    if field_def.value_type == "decimal":
                        curr_res = normalize_currency_amount(raw_val)
                        if curr_res:
                            parsed_val, unit = curr_res
                        else:
                            parsed_val = parse_decimal(raw_val)
                    elif field_def.value_type == "date":
                        parsed_val = normalize_date(raw_val)
                    elif field_def.value_type == "quantity":
                        day_res = normalize_day_count(raw_val)
                        if day_res:
                            parsed_val, unit = day_res
                        else:
                            parsed_val = parse_decimal(raw_val)
                    elif field_def.value_type == "boolean":
                        parsed_val = normalize_boolean(raw_val)
                    elif field_def.value_type == "integer":
                        dec = parse_decimal(raw_val)
                        parsed_val = int(dec) if dec is not None else None

                    if parsed_val is None:
                        continue

                    # Detect period if present (e.g., FY2025, 2026, Q3)
                    period = None
                    period_match = re.search(r"\b(FY\d{4}|20\d{2}-Q[1-4]|Q[1-4]\s*20\d{2}|20\d{2})\b", content)
                    if period_match:
                        period = period_match.group(1).replace(" ", "")

                    evidence_span = EvidenceSpan(
                        document_id=document_id,
                        tenant_id=tenant_id,
                        chunk_id=chunk_id,
                        page_number=page_number,
                        start_offset=s_off,
                        end_offset=e_off,
                        quoted_text=full_match_text,
                    )

                    fact_id = f"fact-{uuid.uuid4().hex[:12]}"
                    fact = ExtractedFact(
                        fact_id=fact_id,
                        tenant_id=tenant_id,
                        document_id=document_id,
                        subject=target_subject,
                        attribute=field_def.attribute,
                        value=parsed_val,
                        raw_value=raw_val,
                        value_type=field_def.value_type,
                        unit=normalize_unit(unit),
                        period=period,
                        evidence=(evidence_span,),
                        confidence=0.95,
                    )
                    extracted.append(fact)
                    break  # Matched this pattern for this field

        return extracted

    def extract_document_facts(
        self,
        tenant_id: str,
        document_id: str,
        passages: Sequence[Dict[str, Any]],
        schema_name: str = "contract_terms",
        custom_schema: Optional[ExtractionSchema] = None,
        subject: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Execute schema-guided extraction over all passages of a document.
        passages: List of dicts containing 'chunk_id', 'text', and optional 'page_number'.
        """
        schema = custom_schema or self.schemas.get(schema_name)
        if not schema:
            return ExtractionResult(
                status="failed",
                document_id=document_id,
                tenant_id=tenant_id,
                errors=(f"Unknown extraction schema: {schema_name}",),
            )

        facts_list: List[ExtractedFact] = []
        errors: List[str] = []

        seen_keys = set()
        for p in passages:
            chunk_id = str(p.get("chunk_id", f"chk-{uuid.uuid4().hex[:8]}"))
            text = str(p.get("text", ""))
            page_no = p.get("page_number")

            if not text.strip():
                continue

            try:
                chunk_facts = self.extract_from_chunk(
                    tenant_id=tenant_id,
                    document_id=document_id,
                    chunk_id=chunk_id,
                    content=text,
                    schema=schema,
                    page_number=page_no,
                    subject_override=subject,
                )
                for f in chunk_facts:
                    key = (f.subject, f.attribute, f.period)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        facts_list.append(f)
            except Exception as exc:
                errors.append(f"Extraction error in chunk {chunk_id}: {exc}")

        status_label = "completed" if not errors else ("partial" if facts_list else "failed")
        return ExtractionResult(
            status=status_label,
            document_id=document_id,
            tenant_id=tenant_id,
            facts=tuple(facts_list),
            errors=tuple(errors),
            schema_name=schema.schema_name,
            schema_version=schema.schema_version,
        )
