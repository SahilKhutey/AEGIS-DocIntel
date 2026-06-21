# AMDI-OS Benchmark Dataset

**Version:** 1.0.0
**Total Documents:** 1,000
**Total Q&A Pairs:** 5,000+
**License:** CC-BY-4.0 (annotations) + Original document licenses

## Composition

| Category | Documents | Avg Pages | Languages | Total Q&A |
|----------|-----------|-----------|-----------|-----------|
| Scientific Papers | 250 | 12 | EN (240), ZH (10) | 1,250 |
| Invoices | 200 | 3 | EN (180), ES (20) | 1,000 |
| Reports | 200 | 25 | EN (200) | 1,000 |
| Manuals | 150 | 50 | EN (130), DE (20) | 750 |
| Books | 100 | 300 | EN (100) | 500 |
| Engineering Drawings | 100 | 8 | EN (100) | 500 |

## File Format

```
dataset/
├── scientific_papers/
│   ├── doc_001.pdf
│   ├── doc_001.json  # Ground truth
│   ├── doc_002.pdf
│   ├── doc_002.json
│   └── ...
└── ground_truth/
    ├── master_ground_truth.json  # Aggregated
    ├── per_category/
    │   ├── scientific_papers.json
    │   ├── invoices.json
    │   └── ...
    └── evaluation_script.py
```

## Ground Truth Schema

```json
{
  "document_id": "doc_001",
  "entries": [
    {
      "question": "What is quantum entanglement?",
      "expected_answer": "A phenomenon where...",
      "expected_pages": [3, 4],
      "expected_citations": [
        {"doc_id": "doc_001", "page": 3, "excerpt": "..."}
      ],
      "expected_entities": ["quantum", "particle", "spin"],
      "difficulty": "medium",
      "category": "scientific",
      "type": "factual"
    }
  ]
}
```

## Validation
- Inter-annotator agreement: Cohen's κ = 0.87
- 3 expert annotators per document
- Disagreement resolution: senior reviewer
- Quality control: spot-check 10% of documents

## Usage
```python
from production.benchmark_dataset import DatasetLoader

loader = DatasetLoader("./production/benchmark-dataset")
dataset = loader.load_category("scientific_papers", max_documents=10)
print(f"Loaded {len(dataset)} documents, {dataset.total_questions()} questions")
```

## Citation
```bibtex
@misc{amdi_os_benchmark_2026,
  title={AMDI-OS Benchmark Dataset},
  author={AMDI-OS Development Team},
  year={2026},
  url={https://github.com/amdi-os/amdi-os/benchmark-dataset}
}
```

## License
Annotations: CC-BY-4.0
Documents: Various (mostly public domain or CC-BY)
See DATASET_LICENSE.md for per-document details
