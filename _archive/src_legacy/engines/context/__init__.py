'''
AEGIS-MIOS — Context Builder Package
=====================================
Assembles structured chat context for LLM reasoning.
'''

from __future__ import annotations

from typing import Any
from src.engines.context.context_builder import ContextBuilder as BaseContextBuilder, _SYSTEM_PROMPT as SYSTEM_PROMPT
from src.engines.retrieval.amdi_retriever import RetrievalContext, RetrievalResult


class DictLikeBuiltContext(dict):
    '''A dictionary representation that also exposes BuiltContext attributes for compatibility.'''

    def __init__(
        self,
        messages: list[dict],
        tokens_used: int,
        source_map: dict[int, str],
        table_count: int,
        element_count: int,
    ):
        super().__init__({
            'messages': messages,
            'tokens_used': tokens_used,
            'source_map': source_map,
            'table_count': table_count,
            'element_count': element_count,
            'selected_ids': list(source_map.values()),
        })
        self.messages = messages
        self.tokens_used = tokens_used
        self.source_map = source_map
        self.table_count = table_count
        self.element_count = element_count


class ContextBuilder(BaseContextBuilder):
    '''Context builder adapter supporting both standard and workflow signatures.'''

    def build(
        self,
        question: str,
        retrieval_ctx: Any = None,
        history: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> DictLikeBuiltContext:
        '''Assemble prompt messages from retrieved elements and answers.'''
        if retrieval_ctx is None:
            hits = kwargs.get('hits', [])
            ret_results = []
            for rank, h in enumerate(hits, start=1):
                # Handle FusedHit or RetrievalResult
                element = getattr(h, 'element', h)
                score = getattr(h, 'final_score', getattr(h, 'score', 0.5))
                layer_scores = getattr(h, 'layer_scores', {})
                ret_results.append(RetrievalResult(
                    element=element,
                    score=score,
                    layer_scores=layer_scores,
                    rank=rank,
                ))
            tables = kwargs.get('tables', [])
            table_answers = []
            for t in tables:
                if hasattr(t, 'text'):
                    table_answers.append(t.text)
                elif hasattr(t, 'content'):
                    table_answers.append(t.content)
            retrieval_ctx = RetrievalContext(
                query=question,
                query_type='unknown',
                weights={},
                results=ret_results,
                table_answers=table_answers,
                latency_ms=0.0,
            )

        res = super().build(question, retrieval_ctx, history)
        return DictLikeBuiltContext(
            messages=res.messages,
            tokens_used=res.tokens_used,
            source_map=res.source_map,
            table_count=res.table_count,
            element_count=res.element_count,
        )


__all__ = ['ContextBuilder', 'SYSTEM_PROMPT']
