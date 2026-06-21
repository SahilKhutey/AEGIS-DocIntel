"""

Token Usage Benchmark

======================



Tracks token consumption across the pipeline.



Categories:

    - Input tokens (prompts + context)

    - Output tokens (LLM responses)

    - Total tokens

    - Cost-relevant tokens (billable)

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List





@dataclass

class TokenResult:

    """Token usage result."""



    total_input_tokens: int

    total_output_tokens: int

    total_tokens: int

    tokens_by_engine: Dict[str, int] = field(default_factory=dict)

    tokens_by_section: Dict[str, int] = field(default_factory=dict)

    average_per_query: float = 0.0

    num_queries: int = 0

    savings_vs_baseline: float = 0.0  # fraction (0..1)



    def to_dict(self) -> dict:

        return {

            "total_input_tokens": self.total_input_tokens,

            "total_output_tokens": self.total_output_tokens,

            "total_tokens": self.total_tokens,

            "tokens_by_engine": self.tokens_by_engine,

            "tokens_by_section": self.tokens_by_section,

            "average_per_query": round(self.average_per_query, 2),

            "num_queries": self.num_queries,

            "savings_vs_baseline": round(self.savings_vs_baseline, 4),

        }





class TokenUsageBenchmark:

    """Track token consumption across pipeline."""



    PRICING = {

        # USD per 1K tokens (input, output)

        "chatgpt-4o": (0.005, 0.015),

        "chatgpt-4-turbo": (0.010, 0.030),

        "chatgpt-3.5-turbo": (0.0005, 0.0015),

        "gemini-1.5-pro": (0.00125, 0.005),

        "gemini-1.5-flash": (0.000075, 0.0003),

        "claude-3.5-sonnet": (0.003, 0.015),

        "claude-3-opus": (0.015, 0.075),

        "deepseek-chat": (0.00014, 0.00028),

        "qwen-2.5": (0.0007, 0.0007),

        "local": (0.0, 0.0),

    }



    def __init__(self) -> None:

        self.input_tokens = 0

        self.output_tokens = 0

        self.engine_tokens: Dict[str, int] = {}

        self.section_tokens: Dict[str, int] = {}

        self.queries: int = 0

        self.baseline_tokens: int = 0



    def record(

        self,

        input_tokens: int,

        output_tokens: int,

        engine: str = "default",

        section: str = "default",

    ) -> None:

        """Record token usage for a query."""

        self.input_tokens += input_tokens

        self.output_tokens += output_tokens

        self.engine_tokens[engine] = (

            self.engine_tokens.get(engine, 0) + input_tokens + output_tokens

        )

        self.section_tokens[section] = (

            self.section_tokens.get(section, 0) + input_tokens + output_tokens

        )

        self.queries += 1



    def set_baseline(self, baseline_tokens: int) -> None:

        self.baseline_tokens = baseline_tokens



    def result(self) -> TokenResult:

        total = self.input_tokens + self.output_tokens

        avg = total / max(self.queries, 1)

        savings = 0.0

        if self.baseline_tokens > 0:

            savings = max(0.0, 1.0 - total / self.baseline_tokens)

        return TokenResult(

            total_input_tokens=self.input_tokens,

            total_output_tokens=self.output_tokens,

            total_tokens=total,

            tokens_by_engine=dict(self.engine_tokens),

            tokens_by_section=dict(self.section_tokens),

            average_per_query=avg,

            num_queries=self.queries,

            savings_vs_baseline=savings,

        )



    def reset(self) -> None:

        self.input_tokens = 0

        self.output_tokens = 0

        self.engine_tokens.clear()

        self.section_tokens.clear()

        self.queries = 0

        self.baseline_tokens = 0



    @classmethod

    def estimate_cost(cls, input_tokens: int, output_tokens: int, agent: str) -> float:

        """Estimate cost in USD for a query."""

        pricing = cls.PRICING.get(agent, cls.PRICING["local"])

        in_rate, out_rate = pricing

        return (input_tokens / 1000) * in_rate + (output_tokens / 1000) * out_rate
