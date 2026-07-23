'''
AEGIS-MIOS — LLM Package
==========================
Abstraction layer for LLM reasoning and response generation.
'''

from __future__ import annotations

from typing import Any
from src.engines.llm.llm_interface import LLMInterface as BaseLLMInterface, LLMResponse


class DictLikeLLMResponse(LLMResponse):
    '''Subclass of LLMResponse supporting dictionary key access for workflows.'''

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class LLMInterface(BaseLLMInterface):
    '''LLM interface adapter supporting standard workflow and orchestrator signatures.'''

    async def reason(
        self,
        question_or_context: str | Any,
        context: Any = None,
        hits: Any = None,
        tables: Any = None,
        **kwargs: Any,
    ) -> DictLikeLLMResponse:
        '''Run LLM inference and return dict-accessible response.'''
        if context is None:
            # Workflow style: reason(context)
            context = question_or_context
            messages = getattr(context, 'messages', [])
            if not messages and isinstance(context, dict):
                messages = context.get('messages', [])
            question = ''
            if messages:
                question = messages[-1].get('content', '')
        else:
            # Orchestrator style
            question = question_or_context

        resp = await super().reason(
            question=question,
            context=context,
            hits=hits,
            tables=tables,
            **kwargs,
        )
        return DictLikeLLMResponse(
            answer=resp.answer,
            citations=resp.citations,
            confidence=resp.confidence,
            confidence_label=resp.confidence_label,
            grounded=resp.grounded,
            model=resp.model,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
        )

    async def stream(self, context: Any, *args: Any, **kwargs: Any) -> Any:
        '''Stream LLM tokens using the base stream_reason method.'''
        messages = getattr(context, 'messages', [])
        if not messages and isinstance(context, dict):
            messages = context.get('messages', [])
        question = ''
        if messages:
            question = messages[-1].get('content', '')

        async for token in self.stream_reason(question, context, None):
            yield token


__all__ = ['LLMInterface']
