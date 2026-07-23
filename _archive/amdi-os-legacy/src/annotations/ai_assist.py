"""
AEGIS-AMDI-OS — AI-Assisted Annotation
=======================================
Automatically generate annotations using LLM or rule-based methods.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from src.annotations.engine import AnnotationEngine
from src.annotations.models import Annotation, AnnotationPosition, AnnotationType
from src.core.geometric_element import ElementType, GeometricElement

logger = logging.getLogger(__name__)


class AIAnnotationAssistant:
    """
    AI-powered annotation suggestions.

    Methods:
    - Auto-tag based on content patterns
    - Suggest questions about unclear text
    - Verify numerical claims
    - Detect potential errors
    """

    def __init__(self, engine: AnnotationEngine | None = None):
        self.engine = engine or AnnotationEngine()

    # ============================================================
    # AUTO-TAGGING
    # ============================================================

    def auto_tag(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        user_id: str = "ai_assistant",
    ) -> list[str]:
        """Auto-tag elements based on content patterns. Returns created annotation IDs."""
        annotation_ids = []
        for element in elements:
            tags = self._extract_tags(element)
            if tags:
                aid = self.engine.tag_element(
                    doc_id=doc_id,
                    page=element.page,
                    element_id=element.element_id,
                    tags=tags,
                    user_id=user_id,
                )
                annotation_ids.append(aid)
        return annotation_ids

    def _extract_tags(self, element: GeometricElement) -> list[str]:
        """Extract tags from element content."""
        tags = []
        content = element.content.lower()
        # Topic tags
        topic_patterns = {
            "financial": [r"revenue", r"profit", r"cost", r"\$[\d,.]+"],
            "legal": [r"contract", r"agreement", r"clause", r"terms"],
            "technical": [r"algorithm", r"system", r"method", r"model"],
            "scientific": [r"experiment", r"hypothesis", r"study", r"research"],
            "marketing": [r"campaign", r"brand", r"customer", r"market"],
            "operational": [r"process", r"workflow", r"procedure"],
        }
        for tag, patterns in topic_patterns.items():
            if any(re.search(p, content) for p in patterns):
                tags.append(tag)
        # Type-based tags
        type_tags = {
            ElementType.TABLE: ["tabular-data"],
            ElementType.FIGURE: ["visual"],
            ElementType.EQUATION: ["mathematical"],
            ElementType.HEADING: ["section-header"],
            ElementType.LIST_ITEM: ["list"],
        }
        if element.type in type_tags:
            tags.extend(type_tags[element.type])
        return list(set(tags))

    # ============================================================
    # NUMERICAL VERIFICATION
    # ============================================================

    def verify_numerical_claims(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        user_id: str = "ai_assistant",
    ) -> list[str]:
        """Find and flag numerical claims for verification."""
        annotation_ids = []
        # Pattern for numerical claims
        claim_patterns = [
            r"(\w+(?:\s+\w+){0,5})\s+(?:was|is|were|are|reached|totaled)\s+\$?[\d,.]+",
            r"\$[\d,.]+\s+(?:million|billion|thousand)",
            r"(\d+(?:\.\d+)?)\s*%\s+(?:growth|increase|decrease)",
        ]
        for element in elements:
            content = element.content
            for pattern in claim_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    claim = match.group(0).strip()
                    # Flag for verification
                    aid = self.engine.verify_claim(
                        doc_id=doc_id,
                        page=element.page,
                        claim=claim,
                        is_correct=False,  # Mark as needs verification
                        user_id=user_id,
                        element_id=element.element_id,
                    )
                    annotation_ids.append(aid)
        return annotation_ids

    # ============================================================
    # SUGGEST QUESTIONS
    # ============================================================

    def suggest_questions(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        user_id: str = "ai_assistant",
    ) -> list[str]:
        """Suggest questions about ambiguous or unclear content."""
        annotation_ids = []
        ambiguous_patterns = [
            (r"\b(approximately|around|roughly|about)\b", "vague_quantifier"),
            (r"\b(etc\.?|and so on|and others)\b", "incomplete_list"),
            (r"\b(maybe|perhaps|possibly|might)\b", "speculation"),
            (r"\?+", "multiple_questions"),
            (r"\b(unclear|TBD|TODO|XXX)\b", "placeholder"),
        ]
        for element in elements:
            for pattern, reason in ambiguous_patterns:
                if re.search(pattern, element.content, re.IGNORECASE):
                    question = f"This section uses '{reason}' - could you clarify?"
                    aid = self.engine.ask_question(
                        doc_id=doc_id,
                        page=element.page,
                        question=question,
                        user_id=user_id,
                        element_id=element.element_id,
                    )
                    annotation_ids.append(aid)
                    break  # One per element
        return annotation_ids

    # ============================================================
    # DETECT INCONSISTENCIES
    # ============================================================

    def detect_inconsistencies(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        user_id: str = "ai_assistant",
    ) -> list[str]:
        """Find potentially inconsistent numerical claims."""
        annotation_ids = []
        # Extract all numbers
        numbers_by_page: dict[int, list[tuple[float, str]]] = {}
        for element in elements:
            nums = re.findall(r"\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*([%BMK]?)", element.content)
            for num_str, suffix in nums:
                try:
                    value = float(num_str.replace(",", ""))
                    if suffix == "%":
                        value_type = "percent"
                    elif suffix == "B":
                        value *= 1_000_000_000
                        value_type = "absolute"
                    elif suffix == "M":
                        value *= 1_000_000
                        value_type = "absolute"
                    elif suffix == "K":
                        value *= 1_000
                        value_type = "absolute"
                    else:
                        value_type = "absolute"
                    numbers_by_page.setdefault(element.page, []).append(
                        (value, element.content[:100])
                    )
                except ValueError:
                    continue
        # Flag pages with many different magnitudes (possible inconsistency)
        for page, nums in numbers_by_page.items():
            values = [n[0] for n in nums if n[0] > 0]
            if len(values) >= 3:
                magnitudes = [len(str(int(v))) for v in values]
                if max(magnitudes) - min(magnitudes) >= 4:
                    # Significant magnitude differences
                    aid = self.engine.add_note(
                        doc_id=doc_id,
                        page=page,
                        content="⚠️ Possible numerical inconsistency: check magnitude units",
                        user_id=user_id,
                    )
                    annotation_ids.append(aid)
        return annotation_ids

    # ============================================================
    # AI-SUGGESTED INSIGHTS
    # ============================================================

    async def generate_insights(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        llm_call: callable | None = None,
        user_id: str = "ai_assistant",
    ) -> list[str]:
        """
        Use LLM to generate insights as annotations.

        llm_call: async function (prompt: str) -> str
        """
        annotation_ids = []
        if llm_call is None:
            return annotation_ids
        # Group by section
        sections: dict[str, list[GeometricElement]] = {}
        for e in elements:
            sec = e.section or "default"
            sections.setdefault(sec, []).append(e)
        # Generate insight per section
        for section, sec_elements in sections.items():
            text = " ".join(e.content for e in sec_elements[:10])
            if len(text) < 100:
                continue
            prompt = f"""Analyze this document section and provide ONE key insight in 1-2 sentences:

{text[:2000]}

Insight:"""
            try:
                insight = await llm_call(prompt)
                if insight and len(insight) > 10:
                    page = sec_elements[0].page
                    aid = self.engine.add_note(
                        doc_id=doc_id,
                        page=page,
                        content=f"💡 AI Insight: {insight.strip()}",
                        user_id=user_id,
                        color="#22d3ee",
                    )
                    annotation_ids.append(aid)
            except Exception as e:
                logger.warning(f"AI insight generation failed: {e}")
        return annotation_ids

    # ============================================================
    # BATCH OPERATIONS
    # ============================================================

    async def auto_annotate_all(
        self,
        doc_id: str,
        elements: list[GeometricElement],
        enable_insights: bool = False,
        llm_call: callable | None = None,
    ) -> dict:
        """
        Run all AI annotation methods.

        Returns dict with counts/lists per type.
        """
        results = {
            "tags": self.auto_tag(doc_id, elements),
            "numerical_flags": self.verify_numerical_claims(doc_id, elements),
            "questions": self.suggest_questions(doc_id, elements),
            "inconsistencies": self.detect_inconsistencies(doc_id, elements),
            "insights": [],
        }
        if enable_insights and llm_call:
            results["insights"] = await self.generate_insights(doc_id, elements, llm_call)
        return results
