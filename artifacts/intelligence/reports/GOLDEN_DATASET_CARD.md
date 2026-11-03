# AEGIS-DocIntel — Golden Question Dataset Card (v1.0)

> **Dataset ID**: `AEGIS-GOLDEN-QUESTIONS-V1.0`  
> **Total Records**: 130 human-reviewed questions  
> **Partitions**: Development (82), Validation (21), Protected Holdout (27)  
> **Seed**: `20261103` (Deterministic zero-leakage document grouping)  

## Category Distribution
- Direct Factual: 20
- Entity & Metadata: 15
- Numeric & Table-Based: 20
- Temporal Reasoning: 10
- Multi-Hop Reasoning: 15
- Cross-Document Comparison: 10
- Summarization: 10
- Unanswerable & Abstention: 20
- Ambiguous & Conflict Analysis: 10
- **Total**: 130 items

## Verification Policy
- Every answerable question is grounded with exact document ID, page number, and evidence text excerpts.
- Unanswerable questions are classified into distinct refusal modes (NOT_FOUND, INSUFFICIENT_EVIDENCE, RESTRICTED, OUT_OF_SCOPE).
- Conflicting and ambiguous queries require explicit identification of discrepancy or clarification.
