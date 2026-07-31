"""TF-IDF frequency retrieval."""

from __future__ import annotations

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query


class FrequencyMethod(BaseRetrievalMethod):
    name = "frequency"

    def __init__(self, store, max_features: int = 50_000, ngram_range=(1, 2)) -> None:
        super().__init__()
        self._store = store
        self._vectorizer = None
        self._matrix = None
        self._unit_ids: list[str] = []
        self._max_features = max_features
        self._ngram = ngram_range

    async def warmup(self) -> None:
        units = await self._store.all_units()
        if not units:
            return
        self._unit_ids = [u.unit_id for u in units]
        docs = [u.text for u in units]
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer(
                max_features=self._max_features,
                ngram_range=self._ngram,
                sublinear_tf=True,
            )
            self._matrix = self._vectorizer.fit_transform(docs)
        except Exception:
            pass

    async def search(self, query: Query, k: int) -> list[Evidence]:
        if self._vectorizer is None or self._matrix is None:
            await self.warmup()
            if self._vectorizer is None or self._matrix is None:
                return []
        try:
            from sklearn.metrics.pairwise import linear_kernel
            vec = self._vectorizer.transform([query.raw])
            sims = linear_kernel(vec, self._matrix).ravel()
            top = sorted(enumerate(sims), key=lambda x: -x[1])[:k]
            out: list[Evidence] = []
            for local_idx, s in top:
                if s <= 0:
                    continue
                unit = await self._store.get_unit(self._unit_ids[local_idx])
                if unit is None:
                    continue
                out.append(Evidence(
                    text=unit.text,
                    score_frequency=float(s),
                    citations=[Citation(
                        document_id=unit.document_id,
                        page=unit.page,
                        bbox=unit.bbox,
                        section=unit.section,
                        method_votes=[self.name],
                    )],
                    metadata={"unit_id": unit.unit_id},
                ))
            return out
        except Exception:
            return []


__all__ = ["FrequencyMethod"]
