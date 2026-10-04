"""
Export Token Budget
==================

Manages token allocation across the exported context for each AI agent.
Each agent has different context window sizes:

    ChatGPT-4 Turbo    128K tokens
    ChatGPT-4o         128K tokens
    Gemini 1.5 Pro     1M tokens
    Claude 3.5 Sonnet  200K tokens
    DeepSeek-V3        64K tokens
    Qwen-2.5           32K tokens
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


AGENT_TOKEN_LIMITS: Dict[str, int] = {
    "chatgpt-4-turbo": 128_000,
    "chatgpt-4o": 128_000,
    "chatgpt-3.5-turbo": 16_000,
    "gemini-1.5-pro": 1_000_000,
    "gemini-1.5-flash": 1_000_000,
    "claude-3.5-sonnet": 200_000,
    "claude-3-opus": 200_000,
    "deepseek-v3": 64_000,
    "qwen-2.5": 32_000,
    "local-default": 8_000,
}


@dataclass
class ExportTokenBudget:
    """
    Token budget for export.

    Attributes
    ----------
    agent : str
        Target agent identifier.
    max_tokens : int
        Maximum tokens allowed.
    system_reserve : int
        Reserved for system prompt.
    summary_budget : int
        Tokens for summary.
    content_budget : int
        Tokens for main content.
    citations_budget : int
        Tokens for citations.
    safety_margin : float
        Fraction of budget kept as safety margin.
    """

    agent: str = "chatgpt-4o"
    max_tokens: int = 128_000
    system_reserve: int = 500
    summary_budget: int = 1000
    content_budget: int = 124_000
    citations_budget: int = 1000
    safety_margin: float = 0.05

    @classmethod
    def for_agent(cls, agent: str) -> "ExportTokenBudget":
        """Create a budget for a specific agent."""
        max_t = AGENT_TOKEN_LIMITS.get(agent, 8_000)
        return cls(agent=agent, max_tokens=max_t)

    def effective_limit(self) -> int:
        """Effective limit after safety margin."""
        return int(self.max_tokens * (1 - self.safety_margin))

    def total_allocated(self) -> int:
        return (
            self.system_reserve
            + self.summary_budget
            + self.content_budget
            + self.citations_budget
        )

    def fits(self, total_tokens: int) -> bool:
        return total_tokens <= self.effective_limit()


class TokenAllocator:
    """
    Allocates tokens across export sections dynamically based on content.
    """

    def __init__(self, budget: ExportTokenBudget) -> None:
        self.budget = budget

    def allocate(
        self,
        system_tokens: int,
        summary_tokens: int,
        content_tokens: int,
        citations_tokens: int,
    ) -> ExportTokenBudget:
        """
        Adjust budget to fit content (preserving proportional weights).
        """
        total = system_tokens + summary_tokens + content_tokens + citations_tokens
        limit = self.budget.effective_limit()
        if total <= limit:
            return self.budget
        # scale down content (largest variable section)
        scale = (
            limit
            - self.budget.system_reserve
            - self.budget.summary_budget
            - self.budget.citations_budget
        ) / max(content_tokens, 1)
        scale = max(0.1, min(1.0, scale))
        new_budget = ExportTokenBudget(
            agent=self.budget.agent,
            max_tokens=self.budget.max_tokens,
            system_reserve=self.budget.system_reserve,
            summary_budget=self.budget.summary_budget,
            content_budget=int(self.budget.content_budget * scale),
            citations_budget=self.budget.citations_budget,
            safety_margin=self.budget.safety_margin,
        )
        return new_budget