# aegis-docprep

Three focused, independently-useful pre-LLM document-structuring primitives, extracted from the AEGIS-DocIntel platform because they represent the components with the strongest real-world validation:

- **PII redaction & compliance filtering** — detects SSNs, credit cards (Luhn mod-10 validated), phone numbers, and person names, allowing you to scrub sensitive or regulated data before it reaches a third-party LLM API.
- **Submodular context packing** — fits the most *relevant* and *diverse* combination of chunks into a fixed token budget, using a provably \((1 - 1/e)\)-bound greedy algorithm rather than naive truncation or similarity-only ranking.
- **Spatial reading-order extraction** — reconstructs the correct reading order of multi-column PDFs, tables, or forms using an acyclic directed graph with Kahn's topological sorting, where raw extraction typically scrambles column order.

---

## Installation

```bash
pip install aegis-docprep
```

**Single dependency:** `numpy>=1.26.0`. No heavy ML dependencies, no FastAPI, no bloated frameworks required.

---

## Quick Start

### 1. PII Redaction

```python
from aegis_docprep import detect_pii, apply_redaction_policy

# Detect PII entities in a text string or document element dictionary
text = "Call John Smith at 555-0100, SSN 123-45-6789, card 4532015112830366."
results = detect_pii({"id": "doc1", "text": text})

for r in results:
    print(f"{r.entity_type:<15} {r.text:<20} score={r.score:.2f}")
# Output:
# US_SSN          123-45-6789          score=0.98
# CREDIT_CARD     4532015112830366     score=0.95
# PHONE_NUMBER    555-0100             score=0.90
# PERSON          John Smith           score=0.85

# Apply redaction directly to scrub sensitive spans
redacted_text = apply_redaction_policy(text, results)
print(redacted_text)
# Call <PERSON_REDACTED> at <PHONE_NUMBER_REDACTED>, SSN <US_SSN_REDACTED>, card <CREDIT_CARD_REDACTED>.
```

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

## Theoretical Guarantees

1. **Knapsack Greedy Approximation Bound (Theorem 9.1):** The submodular knapsack selector provides a proven \((1 - 1/e) \approx 0.632\) approximation guarantee for monotone submodular objective functions under knapsack budgets.
2. **Topological Reading-Order Determinism (Theorem 6.2):** Kahn's algorithm with \((y_{\min}, x_{\min}, \text{node\_id})\) priority-queue tie-breaking guarantees strict deterministic reproducibility across any input permutation.
3. **Luhn Mod-10 Verification:** Credit card regex matches are verified with Luhn checksum validation, distinguishing genuine payment cards (confidence \(0.95\)) from arbitrary 16-digit sequences (confidence \(0.55\)).

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
