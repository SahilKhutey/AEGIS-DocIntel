"""Matrix retrieval: precision-tuned for tabular / numerical content."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from amdi.retrieval.index_store import IndexStore


_NUM_RE = re.compile(r"[-+]?\d[\d,\.]*")
_CCY_RE = re.compile(r"[€£¥$]\s?\d|\bUSD\b|\bEUR\b|\bINR\b", re.I)
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\bQ[1-4]\s?\d{4}\b")


class MatrixMethod(BaseRetrievalMethod):
    name = "matrix"

    def __init__(self, store: "IndexStore") -> None:
        super().__init__()
        self._store = store

    async def search(self, query: Query, k: int) -> list[Evidence]:
        units = await self._store.all_units()
        if not units:
            return []

        has_number = bool(_NUM_RE.search(query.raw))
        has_ccy = bool(_CCY_RE.search(query.raw))
        has_date = bool(_DATE_RE.search(query.raw))

        if not (has_number or has_ccy or has_date):
            return []

        candidates: list[tuple[float, object]] = []
        for u in units:
            t = u.text or ""
            num = len(_NUM_RE.findall(t))
            ccy = len(_CCY_RE.findall(t))
            date = len(_DATE_RE.findall(t))
            if num == 0 and ccy == 0 and date == 0:
                continue
            score = 0.0
            if has_number:
                score += min(num, 5) * 0.2
            if has_ccy:
                score += min(ccy, 5) * 0.4
            if has_date:
                score += min(date, 5) * 0.2

            candidates.append((score, u))

        candidates.sort(key=lambda x: -x[0])
        candidates = candidates[:k]

        evidence: list[Evidence] = []
        for s, u in candidates:
            evidence.append(Evidence(
                text=u.text,
                score_matrix=float(min(s, 1.0)),
                citations=[Citation(
                    document_id=u.document_id,
                    page=u.page,
                    bbox=u.bbox,
                    section=u.section,
                    method_votes=[self.name],
                )],
                metadata={"unit_id": u.unit_id, "numeric": True},
            ))
        return evidence


__all__ = ["MatrixMethod"]
