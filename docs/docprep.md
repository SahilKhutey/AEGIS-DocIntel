# aegis-docprep: Core Document Primitives

`aegis-docprep` is a small, dependency-light package (only `numpy`) extracted from AEGIS-DocIntel. It provides three document-preprocessing primitives: PII detection/redaction, relevance-aware context packing, and spatial reading-order extraction.

> **Status: alpha, not yet published to PyPI.** Install from a clone of the repository (below). Every Python example on this page is executed by the project's test suite, and every documented output is compared with the real output, so these examples cannot silently drift from the code.

---

## Key Features

1. **PII detection & redaction** — US SSNs, Luhn-validated credit-card numbers, phone numbers (US, international, local), email addresses, API keys/tokens, and Title-Case person names. A first-pass filter, not a guarantee (see [Limitations](#limitations-verified)).
2. **Context packing** — cost-benefit greedy selection of the most relevant, diverse chunks within a token budget with proven $(1 - 1/e)/2$ approximation guarantee (see [Guarantees](#guarantees-what-is-and-is-not-proven)).
3. **Reading-order extraction** — sorts multi-column text blocks into natural reading order using 2D geometry and a deterministic topological sort.

---

## Installation

`aegis-docprep` has one external dependency: `numpy`.

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
pip install ./AEGIS-DocIntel/aegis-docprep
```

---

## Quickstart

### 1. PII Redaction

```python
from aegis_docprep import detect_pii, apply_redaction_policy

text = "Our customer, John Smith, phone 555-123-4567, SSN 123-45-6789, card 4532015112830366."

# Detect PII entities in a text string or document element dictionary
results = detect_pii({"id": "doc1", "text": text})
for r in results:
    print(f"{r.entity_type:<15} {r.text:<20} score={r.score:.2f}")
# Output:
# US_SSN          123-45-6789          score=0.98
# CREDIT_CARD     4532015112830366     score=0.95
# PHONE_NUMBER    555-123-4567         score=0.90
# PERSON          John Smith           score=0.85

# Apply redaction directly to scrub sensitive spans
print(apply_redaction_policy(text, results))
# Output:
# Our customer, <PERSON_REDACTED>, phone <PHONE_NUMBER_REDACTED>, SSN <US_SSN_REDACTED>, card <CREDIT_CARD_REDACTED>.
```

### Limitations (verified)

Every item below was reproduced against the current code (the examples in this README are executed by the test suite, so they cannot silently drift).

- **Detected:** US SSNs (`123-45-6789`); credit-card numbers (Luhn-valid → score 0.95; Luhn-*invalid* 16-digit numbers are still flagged, at 0.55); phone numbers (US area-code, international E.164 e.g. `+44 20 7946 0958`, and local 7-digit e.g. `555-0100`); email addresses (`user@domain.com`); API keys and tokens (`sk-...`, `AKIA...`, `ghp_...`); Title-Case person names (2–3 words, with non-name prefix stripping e.g. `Customer John Smith` -> `John Smith`).
- **Not detected:** passport / driver-licence / bank-account numbers; lowercase or single-word names.
- Do not use this as the only control before sending data to a third party.

### 2. Submodular Context Packing

```python
from aegis_docprep.context_packer import SubmodularKnapsackPacker, ContextChunk

# Define candidate chunks with token costs and relevance scores
chunks = [
    ContextChunk(chunk_id="c1", text="Q3 revenue grew 14% to $2.4B.", relevance_score=0.95, token_cost=10),
    ContextChunk(chunk_id="c2", text="The company updated its dress code.", relevance_score=0.10, token_cost=10),
    ContextChunk(chunk_id="c3", text="Operating margins expanded by 220 bps.", relevance_score=0.90, token_cost=10),
    ContextChunk(chunk_id="c4", text="New recycling bins were added to floor 3.", relevance_score=0.15, token_cost=10),
]

# Pack into a 20-token context window
packer = SubmodularKnapsackPacker(alpha=0.6, beta=0.4)
result = packer.pack_context(chunks, max_budget=20)

print(f"Total tokens used: {result.total_tokens} / 20")
print(f"Selected chunks: {[c.chunk_id for c in result.selected_chunks]}")
# Output:
# Total tokens used: 20 / 20
# Selected chunks: ['c1', 'c3']
```

> **API Note:** Call `packer.pack_context(chunks, max_budget)` or its shorthand `packer.pack(chunks, max_budget)`. Chunks specify `token_cost` (or `token_count`).

### 3. Spatial Reading-Order Extraction

```python
from aegis_docprep import SpatialReadingGraph

# Elements extracted from a document with normalized bounding boxes (x, y, w, h in [0, 1])
# Given in shuffled / scrambled order:
elements = [
    {"id": "footer", "x": 0.1, "y": 0.80, "w": 0.8, "h": 0.05, "text": "Page 1 Footer"},
    {"id": "col_b1", "x": 0.55, "y": 0.15, "w": 0.35, "h": 0.1, "text": "Right col item 1"},
    {"id": "col_a1", "x": 0.1, "y": 0.15, "w": 0.35, "h": 0.1, "text": "Left col item 1"},
    {"id": "title", "x": 0.1, "y": 0.05, "w": 0.8, "h": 0.05, "text": "Annual Report"},
    {"id": "col_a2", "x": 0.1, "y": 0.30, "w": 0.35, "h": 0.1, "text": "Left col item 2"},
    {"id": "col_b2", "x": 0.55, "y": 0.30, "w": 0.35, "h": 0.1, "text": "Right col item 2"},
]

graph = SpatialReadingGraph()
ordered_elements = graph.extract_reading_order(elements)

print([el["id"] for el in ordered_elements])
# Output:
# ['title', 'col_a1', 'col_b1', 'col_a2', 'col_b2', 'footer']
```


---

## Guarantees (what is and is not proven)

1. **Context packing — (1 − 1/e)/2 approximation guarantee.** The packer uses modified density-greedy selection with a best-single-item fallback: it returns the better of the greedy set and the single best feasible chunk $\max_{i: c_i \le B} F(\{i\})$. This achieves the standard $(1 - 1/e)/2 \approx 0.316$ approximation factor for monotone submodular knapsack (verified in `tests/test_packer_guarantee_gap.py`). Earlier claims of an unconstrained $(1 - 1/e)$ bound without the fallback were incorrect.
2. **Reading-order determinism:** a fixed tie-break rule gives a reproducible order for a given input.
3. **Luhn validation:** credit-card matches are checksum-validated (valid → 0.95, invalid → 0.55, still flagged).

---

## Framework integration

### LangChain (document transformer)

Verified manually against `langchain-core` 1.6.7; not run in CI because `langchain-core` is not a dependency of this project.

<!-- doc-test: skip reason="needs langchain-core (verified manually against langchain-core 1.6.7); not installed in CI" -->
```python
from typing import Sequence

from langchain_core.documents import Document
from langchain_core.documents.transformers import BaseDocumentTransformer
from aegis_docprep import apply_redaction_policy, detect_pii


class AegisPIITransformer(BaseDocumentTransformer):
    def transform_documents(self, documents: Sequence[Document], **kwargs) -> Sequence[Document]:
        out = []
        for doc in documents:
            found = detect_pii({"id": str(doc.metadata.get("id", "")), "text": doc.page_content})
            out.append(Document(page_content=apply_redaction_policy(doc.page_content, found), metadata=doc.metadata))
        return out
```

A LlamaIndex example was removed: it called APIs that do not exist and could not be verified. It will return once it is tested against a real install.

---

## Verification (testing)

```bash
cd aegis-docprep
pip install -e ".[dev]"
pytest tests/
```
