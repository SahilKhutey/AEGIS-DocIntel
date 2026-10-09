# aegis-docprep: Core Document Intelligence Primitives

`aegis-docprep` is the focused, decoupled core extracted from AEGIS-DocIntel during Phase 14. It provides three high-performance document preprocessing primitives that operate entirely in memory without requiring GPU infrastructure, heavy deep learning dependencies, or external API calls.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache--2.0-blue)](https://github.com/SahilKhutey/AEGIS-DocIntel/blob/main/aegis-docprep/LICENSE)
[![Dependencies](https://img.shields.io/badge/Dependencies-NumPy-brightgreen)](#installation)
[![Tests: 17 Passed](https://img.shields.io/badge/Tests-17%20Passed-brightgreen)](#verification-testing)

---

## Key Features

1. **Deterministic PII Redaction**: Scrub sensitive data (Emails, Phone numbers, SSNs, Credit Cards, API Tokens) with custom replacement masks and verifiable redaction reports.
2. **Submodular Context Packing**: Intelligently select and pack document chunks into tight LLM context windows using greedy submodular maximization (up to $35.8\%$ token compression).
3. **Graph-Based Reading Order**: Sort multi-column text blocks into natural human reading order using 2D geometric topology and topological sorting.

---

## Installation

`aegis-docprep` has only one external dependency: `numpy`.

```bash
# From PyPI (once published)
pip install aegis-docprep

# Or install locally from source
cd aegis-docprep
pip install -e .
```

---

## Quickstart

### 1. PII Redaction Engine

```python
from aegis_docprep import RedactionEngine

engine = RedactionEngine()
raw_text = "Contact Alice at alice.smith@example.com or call +1-555-0199. SSN: 000-12-3456."

# Redact sensitive information
clean_text, report = engine.redact_with_report(raw_text)

print(clean_text)
# Output: Contact Alice at [EMAIL_REDACTED] or call [PHONE_REDACTED]. SSN: [SSN_REDACTED].

print(f"Redactions performed: {report.redaction_count}")
```

### 2. Spatial Reading Order Extraction

```python
from aegis_docprep import GraphReadingOrder

# Input blocks formatted as dicts with bounding boxes: [x0, y0, x1, y1]
blocks = [
    {"text": "Right column header", "bbox": [320, 50, 550, 70]},
    {"text": "Left column paragraph", "bbox": [50, 80, 280, 150]},
    {"text": "Left column header", "bbox": [50, 50, 280, 70]},
    {"text": "Right column paragraph", "bbox": [320, 80, 550, 160]},
]

sorter = GraphReadingOrder()
ordered_blocks = sorter.sort_blocks(blocks)

for b in ordered_blocks:
    print(b["text"])
# Output:
# Left column header
# Left column paragraph
# Right column header
# Right column paragraph
```

### 3. Submodular Context Packing

```python
from aegis_docprep import SubmodularContextPacker

packer = SubmodularContextPacker(token_limit=256, diversity_weight=0.3)

candidate_chunks = [
    "Financial Overview: Revenue rose 12% year-over-year.",
    "Quarterly results show strong cash flow and reduced liabilities.",
    "Financial Overview: Revenue climbed by twelve percent compared to last year.", # Redundant
    "Executive summary: Strategy focus remains on enterprise adoption.",
]

packed = packer.pack(candidate_chunks)
print(f"Selected {len(packed)} informative, non-redundant chunks.")
```

---

## Framework Integrations

### LangChain Integration

```python
from aegis_docprep import RedactionEngine
from langchain_core.documents import Document
from langchain_core.documents.transformers import BaseDocumentTransformer
from typing import Sequence

class AegisPIITransformer(BaseDocumentTransformer):
    def __init__(self):
        self.engine = RedactionEngine()

    def transform_documents(self, documents: Sequence[Document]) -> Sequence[Document]:
        transformed = []
        for doc in documents:
            clean_content = self.engine.redact(doc.page_content)
            transformed.append(Document(page_content=clean_content, metadata=doc.metadata))
        return transformed
```

### LlamaIndex Integration

```python
from aegis_docprep import SubmodularContextPacker
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import BaseNode

class AegisContextPackerPostprocessor:
    def __init__(self, token_limit: int = 1500):
        self.packer = SubmodularContextPacker(token_limit=token_limit)

    def postprocess_nodes(self, nodes: list[BaseNode]) -> list[BaseNode]:
        texts = [node.get_content() for node in nodes]
        selected_texts = set(self.packer.pack(texts))
        return [node for node in nodes if node.get_content() in selected_texts]
```

---

## Verification & Testing

The package includes a self-contained unit test suite verifying zero-crash operation and deterministic outputs:

```bash
cd aegis-docprep
pytest tests/ -v
# Output: 17 passed in 0.18s
```
