"""
aegis.intelligence.citations.claim_extractor
============================================
Deconstructs multi-sentence or compound answers into atomic, verifiable factual claims.
"""

from __future__ import annotations

import re
import uuid
from typing import List

from aegis.intelligence.models import ClaimItem, ClaimSupportStatus


class ClaimExtractor:
    """Extracts atomic factual claims from text."""

    # Conjunctions and punctuation splitting compound clauses
    SPLIT_PATTERNS = re.compile(
        r"(?<=[.!?])\s+|(?<=[,;])\s+(?:and|while|whereas|furthermore|additionally|but)\s+",
        re.IGNORECASE,
    )

    @classmethod
    def extract_claims(cls, answer_text: str) -> List[ClaimItem]:
        """Deconstruct answer text into atomic ClaimItem records."""
        raw_text = answer_text.strip()
        if not raw_text:
            return []

        # Split into sentences and independent clauses
        segments = cls.SPLIT_PATTERNS.split(raw_text)
        claims: List[ClaimItem] = []

        for seg in segments:
            cleaned = seg.strip().rstrip(".;,")
            if not cleaned or len(cleaned) < 5:
                continue
            # Filter non-factual greetings or filler phrases
            if cleaned.lower() in [
                "in conclusion",
                "to summarize",
                "based on the documents",
                "as stated above",
            ]:
                continue

            claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
            claims.append(
                ClaimItem(
                    claim_id=claim_id,
                    text=cleaned,
                    citations=[],
                    support_status=ClaimSupportStatus.UNSUPPORTED,
                )
            )

        if not claims and raw_text:
            claims.append(
                ClaimItem(
                    claim_id=f"CLM-{uuid.uuid4().hex[:8].upper()}",
                    text=raw_text,
                    citations=[],
                    support_status=ClaimSupportStatus.UNSUPPORTED,
                )
            )

        return claims
