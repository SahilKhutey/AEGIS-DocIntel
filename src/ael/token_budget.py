'''
AEGIS-AEL — Token Budget Manager
==================================
TB = B - U

Audit note (Repository Audit, Finding 2): the previous module-level
`tiktoken.get_encoding('cl100k_base')` call performed a network fetch with no
try/except and no offline fallback, so importing this module crashed the
entire application in any network-restricted environment (air-gapped or
VPC-egress-restricted deployments, which are common for AEGIS's stated
regulated-industry target market). `_load_encoding()` below fixes this with a
three-tier fallback: a locally vendored BPE file, then the normal network
fetch, then a character-count-based approximate encoder that keeps the
application running (with reduced token-count precision) rather than crashing.
'''
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Iterable

logger = logging.getLogger('amdi.ael.token_budget')

# Default location for a pre-vendored cl100k_base.tiktoken BPE file. Populate
# this at Docker-image build time (a one-time network fetch during CI/build,
# not at application runtime) so production containers never need runtime
# network access for tokenization. See docs/deployment/vendoring-tiktoken.md.
_DEFAULT_VENDOR_PATH = os.path.join(
    os.path.dirname(__file__), '_vendor', 'cl100k_base.tiktoken'
)


class _ApproximateEncoding:
    '''
    Degraded-mode stand-in for a tiktoken Encoding, used only when neither a
    vendored BPE file nor network access is available. Approximates token
    count at ~4 characters per token (a widely-used rough heuristic for
    English text) and supports the same encode()/decode() shape the rest of
    this module relies on, so callers do not need to branch on which
    encoding backend is active.
    '''

    name = 'approximate-char4'
    CHARS_PER_TOKEN = 4

    def encode(self, text: str, disallowed_special: tuple = ()) -> list[str]:
        # Represent each pseudo-token as a fixed-width character slice so
        # decode() can reconstruct the original text exactly for any prefix
        # (needed by truncate_to_fit's tokens[:max_t] slicing).
        return [
            text[i:i + self.CHARS_PER_TOKEN]
            for i in range(0, len(text), self.CHARS_PER_TOKEN)
        ]

    def decode(self, tokens: list[str]) -> str:
        return ''.join(tokens)


# Static cl100k_base metadata, copied directly from tiktoken_ext.openai_public
# (tiktoken's own installed source, not a network fetch) so the vendored-file
# path below never needs `tiktoken.get_encoding('cl100k_base')` to succeed —
# that call is exactly the network-dependent operation vendoring exists to
# avoid. Only `mergeable_ranks` (the actual BPE data, hashes/proprietary
# content) needs to come from the vendored file; the pattern string and
# special-token IDs are small, public, static constants safe to inline here.
_CL100K_PAT_STR = (
    r"'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| "
    r"?[^\s\p{L}\p{N}]++[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"
)
_CL100K_SPECIAL_TOKENS = {
    '<|endoftext|>': 100257,
    '<|fim_prefix|>': 100258,
    '<|fim_middle|>': 100259,
    '<|fim_suffix|>': 100260,
    '<|endofprompt|>': 100276,
}


def _load_encoding(vendor_path: str | None = None):
    '''
    Loads the cl100k_base encoding via a three-tier fallback:
      1. A locally vendored BPE file (no network access required at all —
         uses the static _CL100K_PAT_STR/_CL100K_SPECIAL_TOKENS constants
         above rather than fetching them from tiktoken.get_encoding()).
      2. The normal tiktoken network fetch (unchanged behavior when network
         access is available and no vendored file has been provisioned).
      3. A character-count-based approximate encoder, so the application
         starts and remains usable — with a logged warning and reduced
         token-count precision — rather than crashing outright.
    '''
    try:
        import tiktoken
        import tiktoken.load  # noqa: F401
    except ImportError:
        logger.warning(
            'tiktoken module is not installed. Falling back to approximate '
            'character-count-based token estimator.'
        )
        return _ApproximateEncoding()

    path = vendor_path or os.environ.get('AEGIS_TIKTOKEN_VENDOR_PATH', _DEFAULT_VENDOR_PATH)

    if os.path.exists(path):
        try:
            mergeable_ranks = tiktoken.load.load_tiktoken_bpe(path)
            enc = tiktoken.Encoding(
                name='cl100k_base_vendored',
                pat_str=_CL100K_PAT_STR,
                mergeable_ranks=mergeable_ranks,
                special_tokens=_CL100K_SPECIAL_TOKENS,
            )
            logger.info('Loaded tiktoken cl100k_base encoding from vendored file '
                         '(fully offline, no network call made): %s', path)
            return enc
        except Exception as e:
            logger.warning('Vendored tiktoken file at %s failed to load (%s); '
                            'falling back to network fetch.', path, e)

    try:
        enc = tiktoken.get_encoding('cl100k_base')
        logger.info('Loaded tiktoken cl100k_base encoding via network fetch.')
        return enc
    except Exception as e:
        logger.error(
            'Failed to load tiktoken cl100k_base encoding: no vendored file at '
            '%s and network fetch failed (%s). Falling back to an approximate '
            'character-count-based token estimator. Token budgets will be less '
            'precise until a vendored encoding file is provisioned — see '
            'docs/deployment/vendoring-tiktoken.md.', path, e,
        )
        return _ApproximateEncoding()


_ENC = _load_encoding()


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
