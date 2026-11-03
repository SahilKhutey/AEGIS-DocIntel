"""
aegis.intelligence.facts.extractor
==================================
Canonical Fact Extractor extracting typed entities, attributes, numbers, and relationships
while strictly preserving raw character sequences and evidence grounding.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from aegis.intelligence.models import (
    EntityRef,
    FactEvidence,
    FactItem,
    FactObject,
    FactQualifiers,
)


class FactExtractor:
    """Extracts structured facts conforming to schemas/intelligence/fact.schema.json."""

    # Common attribute extraction patterns
    ATTRIBUTE_PATTERNS = [
        # Revenue / Budget
        (r"(?:total\s+)?(?:reported\s+)?(?:revenue|budget|expenditure)\s*(?:(?:is|was|reached|totaled)\s+)?[:]?\s*([\$€₹£]?\s*[\d,]+(?:\.\d+)?\s*(?:million|billion|lakh|crore|k|usd|eur|inr|gbp)?)", "reported_budget", "currency"),
        # Percentage
        (r"(?:growth|grew\s+by|margin|efficiency|increase|reduction|accuracy)\s*(?:(?:of|reached|was|to|by)\s+)?[:]?\s*([\d\.]+\s*%)", "measured_rate", "percentage"),
        # Headcount
        (r"(?:headcount|employees|workforce|personnel)\s*(?:(?:totaled|reached|was)\s+)?[:]?\s*([\d,]+)", "headcount", "quantity"),
        # Date
        (r"(?:completed|effective|commenced|published|dated)\s*(?:on|in)?\s*[:]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{4})", "event_date", "date"),
    ]

    @classmethod
    def extract_from_passage(
        self,
        document_id: str,
        text: str,
        page_number: int = 1,
        chunk_id: Optional[str] = None,
        default_entity: str = "Organization",
        reporting_period: Optional[str] = None,
    ) -> List[FactItem]:
        """Extract facts from a single document passage."""
        facts: List[FactItem] = []
        c_id = chunk_id or f"CHUNK-{uuid.uuid4().hex[:6].upper()}"

        # Detect entity mention in text (capitalized phrases or default)
        ent_match = re.search(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
        entity_name = ent_match.group(1) if ent_match else default_entity
        entity_ref = EntityRef(
            entity_id=f"ENT-{hash(entity_name) & 0xFFFFFF:06X}",
            name=entity_name,
            type="organization_or_project",
        )

        for pattern, predicate, data_type in self.ATTRIBUTE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                raw_val = m.group(1).strip()
                fact_id = f"FACT-{uuid.uuid4().hex[:8].upper()}"

                # Parse numeric value if possible
                num_match = re.search(r"[\d,]+(?:\.\d+)?", raw_val)
                parsed_val: Any = raw_val
                unit: Optional[str] = None

                if num_match:
                    num_str = num_match.group(0).replace(",", "")
                    try:
                        parsed_val = float(num_str) if "." in num_str else int(num_str)
                    except ValueError:
                        parsed_val = raw_val

                # Unit detection
                if "$" in raw_val or "usd" in raw_val.lower():
                    unit = "USD"
                elif "₹" in raw_val or "inr" in raw_val.lower():
                    unit = "INR"
                elif "€" in raw_val or "eur" in raw_val.lower():
                    unit = "EUR"
                elif "%" in raw_val:
                    unit = "%"

                fact_obj = FactObject(
                    value=parsed_val,
                    raw_value=raw_val,
                    unit=unit,
                    data_type=data_type,
                )

                ev = FactEvidence(
                    document_id=document_id,
                    page_number=page_number,
                    chunk_id=c_id,
                    quoted_text=m.group(0),
                )

                qualifiers = FactQualifiers(
                    reporting_period=reporting_period,
                    status="reported",
                )

                facts.append(
                    FactItem(
                        fact_id=fact_id,
                        subject=entity_ref,
                        predicate=predicate,
                        object=fact_obj,
                        qualifiers=qualifiers,
                        evidence=[ev],
                        extraction_method="structured_extraction",
                        confidence=0.95,
                        verification_status="VERIFIED",
                    )
                )

        return facts
