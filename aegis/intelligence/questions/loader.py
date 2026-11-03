"""
aegis.intelligence.questions.loader
===================================
Loads, validates, and queries the canonical Golden Question Dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
import jsonschema

from aegis.intelligence.models import AnswerabilityClass, GoldenQuestion, TaskType


class GoldenQuestionLoader:
    """Manages loading and validation of golden question datasets."""

    def __init__(self, schema_path: Optional[Path | str] = None):
        repo_root = Path.cwd()
        s_path = Path(schema_path) if schema_path else repo_root / "schemas" / "intelligence" / "golden_question.schema.json"
        if s_path.exists():
            self.schema = json.loads(s_path.read_text(encoding="utf-8"))
        else:
            self.schema = None

    def load_jsonl(self, file_path: Path | str, validate_schema: bool = True) -> List[GoldenQuestion]:
        """Load and parse questions from a JSONL file."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Golden questions file not found: {p}")

        questions: List[GoldenQuestion] = []
        with open(p, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                data = json.loads(raw)
                if validate_schema and self.schema:
                    jsonschema.validate(data, self.schema)
                q = GoldenQuestion.model_validate(data)
                questions.append(q)

        return questions

    @staticmethod
    def filter_by_category(questions: List[GoldenQuestion], task_type: TaskType) -> List[GoldenQuestion]:
        """Filter questions by specific task category."""
        return [q for q in questions if q.task_type == task_type]

    @staticmethod
    def filter_by_answerability(
        questions: List[GoldenQuestion], answerability: AnswerabilityClass
    ) -> List[GoldenQuestion]:
        """Filter questions by answerability status."""
        return [q for q in questions if q.answerability == answerability]
