"""The Q&A record schema used by every runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Difficulty = Literal["easy", "medium", "hard", "adversarial"]


@dataclass(slots=True)
class QARecord:
    qid: str
    question: str
    expected_answer: str
    gold_unit_ids: list[str] = field(default_factory=list)
    gold_citations: list[tuple[str, int | None]] = field(default_factory=list)
    difficulty: Difficulty = "medium"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "qid": self.qid,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "gold_unit_ids": list(self.gold_unit_ids),
            "gold_citations": [list(c) for c in self.gold_citations],
            "difficulty": self.difficulty,
            "tags": list(self.tags),
        }


__all__ = ["QARecord", "Difficulty"]
