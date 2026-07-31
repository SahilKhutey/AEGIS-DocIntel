"""Cross-encoder reranker with no-op fallback."""

from __future__ import annotations

import asyncio
import logging

from amdi.retrieval.schemas import Evidence, RetrievalConfig

logger = logging.getLogger("amdi.retrieval.reranker")


class BaseReranker:
    async def score(self, query: str, texts: list[str]) -> list[float]:
        raise NotImplementedError

    async def aclose(self) -> None:
        return None


class NoOpReranker(BaseReranker):
    async def score(self, query: str, texts: list[str]) -> list[float]:
        return [1.0 for _ in texts]


class CrossEncoderReranker(BaseReranker):
    """Cross-encoder reranker using sentence-transformers."""

    def __init__(self, config: RetrievalConfig) -> None:
        self._config = config
        self._model = None

    async def _ensure_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder  # type: ignore
            self._model = CrossEncoder(
                self._config.reranker_model,
                device=self._config.reranker_device,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("CrossEncoder import failed; falling back: %s", exc)
            self._model = None

    async def score(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        await self._ensure_model()
        if self._model is None:
            return [1.0 for _ in texts]
        pairs = [(query, t) for t in texts]
        loop = asyncio.get_running_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: self._model.predict(  # type: ignore[union-attr]
                pairs,
                batch_size=self._config.reranker_batch_size,
                show_progress_bar=False,
            ),
        )
        return [float(s) for s in scores]


def make_reranker(config: RetrievalConfig) -> BaseReranker:
    if config.enable_reranker:
        return CrossEncoderReranker(config)
    return NoOpReranker()


__all__ = ["BaseReranker", "CrossEncoderReranker", "NoOpReranker", "make_reranker"]
