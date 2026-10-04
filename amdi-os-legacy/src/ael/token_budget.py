'''
AEGIS-AEL — Token Budget Manager
==================================
TB = B - U
'''
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable

import tiktoken

logger = logging.getLogger('amdi.ael.token_budget')
_ENC = tiktoken.get_encoding('cl100k_base')


@dataclass
class BudgetAllocation:
    system_prompt: int = 800
    context: int = 4000
    question: int = 300
    output: int = 1500
    safety_margin: int = 200
    used_system: int = 0
    used_context: int = 0
    used_question: int = 0
    used_output: int = 0

    @property
    def total(self) -> int:
        return (self.system_prompt + self.context + self.question + self.output + self.safety_margin)

    @property
    def used(self) -> int:
        return self.used_system + self.used_context + self.used_question

    @property
    def remaining(self) -> int:
        return self.context - self.used_context

    @property
    def utilization(self) -> float:
        return self.used / max(1, self.total)


def count_tokens(text: str) -> int:
    '''Count tokens in a text string.'''
    return len(_ENC.encode(text, disallowed_special=()))


class TokenBudgetManager:
    '''
    Tracks and allocates token budget across export components.
    '''

    AGENT_MAX_TOKENS = {
        'chatgpt': 128_000,
        'gpt-4o': 128_000,
        'gpt-4o-mini': 128_000,
        'o1-preview': 128_000,
        'o1-mini': 128_000,
        'gemini-1.5-pro': 1_000_000,
        'gemini-1.5-flash': 1_000_000,
        'gemini-2.0-flash': 1_000_000,
        'claude-3-5-sonnet': 200_000,
        'claude-3-opus': 200_000,
        'claude-3-haiku': 200_000,
        'deepseek-v3': 64_000,
        'deepseek-r1': 64_000,
        'qwen-2.5-72b': 128_000,
        'qwen-max': 128_000,
        'vllm': 128_000,
        'local': 32_000,
    }

    def __init__(self, agent: str = 'chatgpt', model: str = 'gpt-4o',
                 target_context: int = 4000, target_output: int = 1500):
        self.agent = agent
        self.model = model
        self.max_tokens = self.AGENT_MAX_TOKENS.get(model, 128_000)
        self.allocation = BudgetAllocation(
            context=min(target_context, self.max_tokens // 2),
            output=min(target_output, self.max_tokens // 4),
        )
        self._excluded: list[tuple[str, int]] = []

    def can_fit(self, text: str) -> bool:
        return count_tokens(text) <= self.allocation.remaining

    def allocate(self, component: str, text: str) -> bool:
        '''Try to allocate tokens for a component. Returns True if successful.'''
        cost = count_tokens(text)
        field_map = {
            'system': 'used_system',
            'context': 'used_context',
            'question': 'used_question',
        }
        if component not in field_map:
            return False
        used_field = field_map[component]
        
        limit_map = {
            'system': 'system_prompt',
            'context': 'context',
            'question': 'question',
        }
        limit_field = limit_map[component]
        
        current = getattr(self.allocation, used_field, 0)
        limit = getattr(self.allocation, limit_field, 0)
        if current + cost > limit:
            self._excluded.append((component, cost))
            return False
        setattr(self.allocation, used_field, current + cost)
        return True

    def truncate_to_fit(self, text: str, max_tokens: int | None = None) -> str:
        '''Truncate text to fit within remaining budget.'''
        max_t = max_tokens or self.allocation.remaining
        tokens = _ENC.encode(text, disallowed_special=())
        if len(tokens) <= max_t:
            return text
        return _ENC.decode(tokens[:max_t])

    def summary(self) -> dict:
        return {
            'agent': self.agent,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'allocation': {
                'system': f'{self.allocation.used_system}/{self.allocation.system_prompt}',
                'context': f'{self.allocation.used_context}/{self.allocation.context}',
                'question': f'{self.allocation.used_question}/{self.allocation.question}',
                'output': f'{self.allocation.output}',
            },
            'utilization': round(self.allocation.utilization, 3),
            'remaining': self.allocation.remaining,
            'excluded_components': self._excluded,
        }
