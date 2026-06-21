"""

Benchmark Dataset Loader

==========================



Loads benchmark datasets (documents + ground truth).



Supported Categories:

    - Scientific Papers

    - Invoices

    - Reports

    - Manuals

    - Books

    - Engineering Drawings

"""



from __future__ import annotations



import json

from dataclasses import dataclass, field

from pathlib import Path

from typing import Any, Dict, List, Optional



from .exceptions import DatasetMissingError

from .ground_truth import GroundTruth, GroundTruthEntry





@dataclass

class BenchmarkDataset:

    """A benchmark dataset (collection of documents + ground truth)."""



    name: str

    category: str

    document_paths: List[str] = field(default_factory=list)

    ground_truths: List[GroundTruth] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)



    def __len__(self) -> int:

        return len(self.ground_truths)



    def total_questions(self) -> int:

        return sum(len(gt.entries) for gt in self.ground_truths)



    def to_dict(self) -> dict:

        return {

            "name": self.name,

            "category": self.category,

            "num_documents": len(self.document_paths),

            "num_ground_truths": len(self.ground_truths),

            "total_questions": self.total_questions(),

            "metadata": self.metadata,

        }





class DatasetLoader:

    """

    Load benchmark datasets from disk.



    Expected directory structure:

        datasets/

        ├── scientific_papers/

        │   ├── doc1.pdf

        │   ├── doc1.json   (ground truth)

        │   └── ...

        ├── invoices/

        ├── reports/

        └── ...

    """



    CATEGORIES = [

        "scientific_papers",

        "invoices",

        "reports",

        "manuals",

        "books",

        "engineering_drawings",

    ]



    def __init__(self, base_path: str = "./datasets") -> None:

        self.base_path = Path(base_path)



    def load_category(

        self,

        category: str,

        max_documents: Optional[int] = None,

    ) -> BenchmarkDataset:

        """Load all documents + ground truths in a category."""

        if category not in self.CATEGORIES:

            raise DatasetMissingError(

                f"Unknown category: {category}. "

                f"Available: {self.CATEGORIES}"

            )

        cat_path = self.base_path / category

        if not cat_path.exists():

            raise DatasetMissingError(

                f"Category directory not found: {cat_path}"

            )

        doc_paths = sorted(cat_path.glob("*.pdf"))

        doc_paths.extend(sorted(cat_path.glob("*.docx")))

        if max_documents is not None:

            doc_paths = doc_paths[:max_documents]



        dataset = BenchmarkDataset(

            name=category,

            category=category,

            metadata={"base_path": str(cat_path)},

        )

        for doc_path in doc_paths:

            dataset.document_paths.append(str(doc_path))

            gt_path = doc_path.with_suffix(".json")

            if gt_path.exists():

                try:

                    gt = GroundTruth.from_file(str(gt_path))

                    dataset.ground_truths.append(gt)

                except Exception:

                    continue

        return dataset



    def load_all(

        self,

        max_documents_per_category: Optional[int] = None,

    ) -> List[BenchmarkDataset]:

        """Load all available categories."""

        datasets = []

        for category in self.CATEGORIES:

            try:

                ds = self.load_category(category, max_documents_per_category)

                datasets.append(ds)

            except DatasetMissingError:

                continue

        return datasets



    def load_synthetic(

        self,

        category: str,

        n_documents: int = 10,

        questions_per_doc: int = 5,

    ) -> BenchmarkDataset:

        """Generate a synthetic dataset (for testing)."""

        import random

        rng = random.Random(42)

        dataset = BenchmarkDataset(

            name=f"synthetic_{category}",

            category=category,

            metadata={"synthetic": True},

        )

        templates = [

            "What is {entity}?",

            "When was {entity} discovered?",

            "How does {entity} work?",

            "List the key components of {entity}.",

            "What is the significance of {entity}?",

        ]

        entities = [

            "quantum entanglement", "neural networks", "DNA replication",

            "black holes", "machine learning", "photosynthesis",

            "relativity", "evolution", "gravity", "electromagnetism",

        ]

        for i in range(n_documents):

            doc_path = f"synthetic://{category}/doc_{i}.pdf"

            gt = GroundTruth(

                document_id=f"doc_{i}",

                document_path=doc_path,

                document_type=category,

                metadata={"synthetic": True},

            )

            for j in range(questions_per_doc):

                entity = rng.choice(entities)

                template = rng.choice(templates)

                question = template.format(entity=entity)

                gt.add_entry(

                    GroundTruthEntry(

                        question=question,

                        expected_answer=f"Expected answer about {entity}.",

                        expected_pages=[rng.randint(1, 10)],

                        difficulty=rng.choice(["easy", "medium", "hard"]),

                        category=category,

                    )

                )

            dataset.document_paths.append(doc_path)

            dataset.ground_truths.append(gt)

        return dataset
