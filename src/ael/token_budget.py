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
    except (ImportError, ModuleNotFoundError) as e:
        logger.warning(
            'tiktoken is not installed (%s). Falling back to an approximate '
            'character-count-based token estimator.', e
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
class TokenAllocation:
    target_context: int = 8192
    system_prompt: int = 800
    context: int = 4000
    question: int = 300
    output: int = 1500
    safety_margin: int = 200
    reserved: int = 0
    query: int = 0
    retrieved_content: int = 0
    used_system: int = 0
    used_context: int = 0
    used_question: int = 0
    used_output: int = 0

    @property
    def used(self) -> int:
        return (
            self.used_system
            + self.used_context
            + self.used_question
            + self.used_output
            + self.query
            + self.reserved
            + self.retrieved_content
        )

    @property
    def remaining(self) -> int:
        ctx_rem = max(0, self.context - self.used_context)
        tgt_rem = max(0, self.target_context - self.used)
        return max(ctx_rem, tgt_rem)

    @property
    def utilization(self) -> float:
        if self.target_context == 0:
            return 0.0
        return self.used / max(1, self.target_context)


def count_tokens(text: str) -> int:
    """Return the exact token count for *text* under cl100k_base."""
    if not text:
        return 0
    return len(_ENC.encode(text, disallowed_special=()))


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate *text* to at most *max_tokens*, preserving exact token boundaries."""
    if not text or max_tokens <= 0:
        return ""
    tokens = _ENC.encode(text, disallowed_special=())
    if len(tokens) <= max_tokens:
        return text
    return _ENC.decode(tokens[:max_tokens])


class TokenBudgetManager:
    """Manages token allocation budgets for LLM context construction."""

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

    def __init__(
        self,
        agent: str = 'chatgpt',
        model: str = 'gpt-4o',
        target_context: int = 8192,
        output_headroom: int = 0,
        target_output: int = 1500,
    ):
        self.agent = agent
        self.model = model
        self.max_tokens = self.AGENT_MAX_TOKENS.get(model, 128_000)
        self.allocation = TokenAllocation(
            target_context=target_context,
            context=target_context,
            reserved=output_headroom,
        )
        self._excluded: list[tuple[str, int]] = []

    def can_fit(self, text: str) -> bool:
        return count_tokens(text) <= self.allocation.remaining

    def allocate(self, component: str, text: str) -> bool:
        cost = count_tokens(text)
        field_map = {
            'system': ('used_system', 'system_prompt'),
            'context': ('used_context', 'context'),
            'question': ('used_question', 'question'),
        }
        if component in field_map:
            used_f, limit_f = field_map[component]
            curr = getattr(self.allocation, used_f, 0)
            limit = getattr(self.allocation, limit_f, 800)
            if curr + cost <= limit:
                setattr(self.allocation, used_f, curr + cost)
                return True
        elif cost <= self.allocation.remaining:
            self.allocation.retrieved_content += cost
            return True
        self._excluded.append((component, cost))
        return False

    def truncate_to_fit(self, text: str, max_tokens: int | None = None) -> str:
        max_t = max_tokens or self.allocation.remaining
        return truncate_to_tokens(text, max_t)

    def summary(self) -> dict:
        return {
            'agent': self.agent,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'utilization': round(self.allocation.utilization, 3),
            'remaining': self.allocation.remaining,
            'excluded_components': self._excluded,
        }

    def set_system_prompt(self, text: str) -> int:
        tokens = count_tokens(text)
        self.allocation.system_prompt = tokens
        return tokens

    def set_query(self, text: str) -> int:
        tokens = count_tokens(text)
        self.allocation.query = tokens
        return tokens

    def allocate_retrieved(self, text: str) -> bool:
        """Attempt to add retrieved content. Returns True if it fits."""
        tokens = count_tokens(text)
        if tokens <= self.allocation.remaining:
            self.allocation.retrieved_content += tokens
            return True
        return False

    def fit_items(
        self, items: Iterable[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """Given (item_id, text) pairs, return as many as fit in remaining budget."""
        result = []
        for item_id, text in items:
            tokens = count_tokens(text)
            if tokens <= self.allocation.remaining:
                self.allocation.retrieved_content += tokens
                result.append((item_id, text))
            else:
                # Try truncating the last item
                avail = self.allocation.remaining
                if avail > 50:  # Only truncate if meaningful room left
                    truncated = truncate_to_tokens(text, avail)
                    self.allocation.retrieved_content += count_tokens(
                        truncated
                    )
                    result.append((item_id, truncated))
                break
        return result
