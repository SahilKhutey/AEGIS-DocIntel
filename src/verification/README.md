# AMDI-OS Verification Engine

The **Verification Engine** serves as the final post-generation quality gate before AI-agent responses are returned to the user or downstream processes.

## Architecture

The engine aggregates multiple validation pipelines:
1. **Citation Verification**: Asserts that all inline and bibliography citations correspond to actual document IDs, page bounds, and section headers with high containment scores.
2. **Fact Verification**: Extracts atomic claims and aligns them lexically with ground-truth records in a local knowledge base.
3. **Consistency Verification**: Performs syntactic contradiction, range order, temporal chronology, and pronoun attribution checks.
4. **Source Verification**: Measures the reliability and metadata presence of ingested sources.
5. **Hallucination Detection**: Flags specific uncited claims, specificity paradoxes, and attributions of entity terms not found in the source documents.

---

## Configuration & Usage

```python
from src.verification import VerificationEngine, ConnectorConfig

# Initialize engine
engine = VerificationEngine(
    min_confidence=0.75,
    strict_citations=False,
    fuzzy_threshold=0.8,
    kb={
        "document.author": "AEGIS Dev Team",
        "system.version": "1.0.0"
    }
)

# Ingested documents
source_documents = {
    "doc_001": {
        "title": "AMDI Engine Manual",
        "text": "The AMDI OS system version 1.0.0 is developed by the AEGIS Dev Team."
    }
}

# AI agent response text
response_text = "[doc_001, p.1] AMDI OS system version 1.0.0 is developed by the AEGIS Dev Team."

# Execute verification
report = engine.verify(
    response_text=response_text,
    source_documents=source_documents
)

print(f"Passed: {report.is_valid}")
print(f"Overall Confidence: {report.overall_confidence}")
print(f"Details: {report.to_dict()}")

# Optional exception check
report.raise_for_status()
```
