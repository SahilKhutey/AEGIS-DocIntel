"""Deterministic fake LLM — no network, no API keys, sub-millisecond."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class StubLLM:
    answers: dict[str, str] = field(default_factory=dict)
    default: str = "I don't know based on the provided evidence."
    temperature: float = 0.0

    def complete(self, prompt: str, *, max_tokens: int = 128) -> str:
        p = prompt.lower()
        for key in sorted(self.answers.keys(), key=len, reverse=True):
            if key.lower() in p:
                return self.answers[key][:max_tokens]
        return self.default[:max_tokens]

    def stream(self, prompt: str, *, max_tokens: int = 128):
        out = self.complete(prompt, max_tokens=max_tokens)
        chunks = re.findall(r"\S+\s*|\s+", out)
        for i, chunk in enumerate(chunks):
            yield chunk, i == len(chunks) - 1


__all__ = ["StubLLM"]
