"""Template retrieval by document-template fingerprint."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from amdi.retrieval.index_store import IndexStore


_HEADING_RE = re.compile(r"^(\d+(\.\d+)*\s+|chapter\s+\d+|#+\s+)", re.I | re.M)
_BULLET_RE = re.compile(r"^\s*[-*•]\s", re.M)


class TemplateMethod(BaseRetrievalMethod):
    name = "template"

    def __init__(self, store: "IndexStore") -> None:
        super().__init__()
        self._store = store

    async def search(self, query: Query, k: int) -> list[Evidence]:
        ql = query.raw.lower()
        structural_intent = any(t in ql for t in (
            "table of contents", "toc", "section headings",
            "outline", "index of", "chapters", "glossary",
        ))
        if not structural_intent:
            return []

        units = await self._store.all_units()
        candidates: list[tuple[float, object]] = []
        for u in units:
            t = u.text or ""
            headings = len(_HEADING_RE.findall(t))
            bullets = len(_BULLET_RE.findall(t))
            if headings < 2 and bullets < 3:
                continue
            density = (headings + 0.2 * bullets) / max(1, len(t) / 200)
            candidates.append((density, u))

        candidates.sort(key=lambda x: -x[0])
        candidates = candidates[:k]
        evidence: list[Evidence] = []
        for s, u in candidates:
            evidence.append(Evidence(
                text=u.text,
                score_template=float(min(s, 1.0)),
                citations=[Citation(
                    document_id=u.document_id,
                    page=u.page,
                    bbox=u.bbox,
                    section=u.section,
                    method_votes=[self.name],
                )],
                metadata={"unit_id": u.unit_id, "structural": True},
            ))
        return evidence


__all__ = ["TemplateMethod"]
