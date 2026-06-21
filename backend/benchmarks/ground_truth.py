"""

Ground Truth Dataset

====================



Defines the expected outputs for benchmark documents.



Each GroundTruthEntry contains:

    - question: the query

    - expected_answer: ground truth answer

    - expected_pages: list of pages where info appears

    - expected_tables: list of relevant table IDs

    - expected_citations: list of citation markers

    - expected_relationships: list of entity pairs

"""



from __future__ import annotations



import json

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Dict, List, Optional



from .exceptions import GroundTruthError





@dataclass

class GroundTruthEntry:

    """A single ground-truth entry."""



    question: str

    expected_answer: str

    expected_pages: List[int] = field(default_factory=list)

    expected_tables: List[str] = field(default_factory=list)

    expected_citations: List[str] = field(default_factory=list)

    expected_relationships: List[Dict[str, str]] = field(default_factory=list)

    expected_entities: List[str] = field(default_factory=list)

    difficulty: str = "medium"  # easy / medium / hard

    category: str = "general"

    metadata: Dict[str, Any] = field(default_factory=dict)



    def to_dict(self) -> dict:

        return {

            "question": self.question,

            "expected_answer": self.expected_answer,

            "expected_pages": self.expected_pages,

            "expected_tables": self.expected_tables,

            "expected_citations": self.expected_citations,

            "expected_relationships": self.expected_relationships,

            "expected_entities": self.expected_entities,

            "difficulty": self.difficulty,

            "category": self.category,

            "metadata": self.metadata,

        }





@dataclass

class GroundTruth:

    """A ground-truth dataset for one document."""



    document_id: str

    document_path: str

    document_type: str

    entries: List[GroundTruthEntry] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)



    def add_entry(self, entry: GroundTruthEntry) -> None:

        self.entries.append(entry)



    def get_by_category(self, category: str) -> List[GroundTruthEntry]:

        return [e for e in self.entries if e.category == category]



    def get_by_difficulty(self, difficulty: str) -> List[GroundTruthEntry]:

        return [e for e in self.entries if e.difficulty == difficulty]



    def to_dict(self) -> dict:

        return {

            "document_id": self.document_id,

            "document_path": self.document_path,

            "document_type": self.document_type,

            "entries": [e.to_dict() for e in self.entries],

            "metadata": self.metadata,

        }



    @classmethod

    def from_file(cls, path: str) -> "GroundTruth":

        """Load from JSON file."""

        p = Path(path)

        if not p.exists():

            raise GroundTruthError(f"Ground truth file not found: {path}")

        try:

            data = json.loads(p.read_text(encoding="utf-8"))

        except json.JSONDecodeError as exc:

            raise GroundTruthError(f"Invalid JSON: {exc}") from exc

        entries = [

            GroundTruthEntry(**e) for e in data.get("entries", [])

        ]

        return cls(

            document_id=data["document_id"],

            document_path=data["document_path"],

            document_type=data["document_type"],

            entries=entries,

            metadata=data.get("metadata", {}),

        )



    def to_file(self, path: str) -> None:

        """Save to JSON file."""

        Path(path).write_text(

            json.dumps(self.to_dict(), indent=2, default=str),

            encoding="utf-8",

        )
