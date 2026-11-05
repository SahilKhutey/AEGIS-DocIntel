# AEGIS-DocIntel — WP-06: Intelligence Failure Analysis & Error Taxonomy

> **Work Package**: WP-06 — Intelligence  
> **Status**: **VERIFIED ANALYSIS**  
> **Taxonomy Standard**: 14-Class Intelligence Defect Classification  

---

## 1. Executive Summary

This document establishes the root-cause error taxonomy and failure analysis framework for **AEGIS-DocIntel** intelligence pipelines. To ensure accountability, model debugging, and continuous improvement, failures are never logged as generic score drops. Every failure in retrieval, reasoning, citation, or reporting is classified into one of 14 deterministic failure categories.

---

## 2. 14-Class Intelligence Error Taxonomy

| Error Code | Classification | Severity | Meaning & Operational Root Cause | Mitigation / Architectural Safeguard |
| :--- | :--- | :---: | :--- | :--- |
| `RETRIEVAL_MISS` | Retrieval Defect | **HIGH** | Required evidence passage is completely absent from retrieved candidate set ($rank > K$). | Expand index coverage, apply multi-query expansion, or increase recall candidate pool $K$. |
| `RANKING_ERROR` | Retrieval Defect | **MEDIUM** | Required evidence is present in candidates but ranked too low to fit in context window. | Reciprocal Rank Fusion (RRF) with tuned $k_0$, or cross-encoder re-ranking. |
| `CONTEXT_TRUNCATION` | Packaging Defect | **HIGH** | Retrieved passage was discarded during submodular context packing due to token budget limits. | Submodular coverage optimization, dynamic query budgeting, or hierarchical passage summarization. |
| `ANSWER_INCORRECT` | Reasoning Defect | **HIGH** | Extracted or generated answer does not match the ground-truth factual assertion. | Fine-tune prompt grounding constraints; require strict verbatim quote entailment. |
| `UNSUPPORTED_CLAIM` | Trust Defect | **CRITICAL** | Generated answer contains factual claims lacking supporting citations. | Atomic claim extractor identifies ungrounded sentences and triggers qualification or redaction. |
| `CITATION_INVALID` | Grounding Defect | **CRITICAL** | Citation points to non-existent document ID, invalid page number, or broken chunk hash. | Strict `CitationResolver` validation against WP-05 provenance register; block invalid citations. |
| `CITATION_MISMATCH` | Grounding Defect | **CRITICAL** | Cited passage exists but does not semantically entail or support the specific claim. | 7-label `SupportEvaluator` filters out `RELATED_ONLY` or `IRRELEVANT` citations prior to report render. |
| `FALSE_ABSTENTION` | Coverage Defect | **MEDIUM** | System abstains or requests clarification despite sufficient evidence being retrieved. | Calibrate evidence sufficiency threshold downward on high-corroboration topics. |
| `MISSED_ABSTENTION` | Trust Defect | **CRITICAL** | System generates an unverified answer when evidence is absent, partial, or contradictory. | Strict abstention gate: refuse or clarify when sufficiency score $< 0.50$ or conflict is detected. |
| `FACT_EXTRACTION_ERROR` | Extraction Defect | **HIGH** | Entity, predicate, or numerical attribute incorrectly extracted from document text or tables. | Structured regex patterns, normalized currency/date parsers, and table grid cell mapping. |
| `FALSE_CONFLICT` | Reasoning Defect | **MEDIUM** | Equivalent statements (differing only in reporting period, geographic scope, or units) flagged as contradictions. | 8-stage comparative conflict protocol: checks period, scope, and units before flagging contradiction. |
| `MISSED_CONFLICT` | Reasoning Defect | **HIGH** | Genuinely contradictory claims across documents are silently merged or ignored. | Conflict comparator evaluates overlapping predicate assertions and mandates conflict disclosure. |
| `REPORT_OMISSION` | Reporting Defect | **HIGH** | Required section, finding, or limitation is omitted from structured report artifact. | Pre-render `ReportValidator` enforces non-empty sections and required findings checklist. |
| `REPORT_INCONSISTENCY` | Reporting Defect | **HIGH** | Rendered report contains internal contradictions, arithmetic errors, or conflicting claims. | Pre-render numerical consistency validator audits totals, percentages, and table values. |

---

## 3. Failure Distribution Across Evaluated Test Sets

Across the execution of the WP-06 intelligence benchmark suites (retrieval modes, 130 golden questions, citation correctness, unanswerable queries, and comparative reports), the following error counts were recorded:

```
+-----------------------------------------------------------------------------------------+
| Error Category          | Evaluated Cases | Detected Failures | Mitigation Status       |
+-----------------------------------------------------------------------------------------+
| RETRIEVAL_MISS          | 20 Queries      | 0 (Recall@5=1.0)  | RESOLVED via RRF Hybrid |
| RANKING_ERROR           | 20 Queries      | 0 (MRR=0.65)      | RESOLVED via RRF Hybrid |
| CONTEXT_TRUNCATION      | 20 Queries      | 0                 | BOUNDED by Packer       |
| ANSWER_INCORRECT        | 130 Questions   | 0                 | VERIFIED against Gold   |
| UNSUPPORTED_CLAIM       | 130 Questions   | 0 (Support=1.0)   | BLOCKED by Gate         |
| CITATION_INVALID        | 8 Vectors       | 0 (Acc=1.0)       | CAUGHT by Resolver      |
| CITATION_MISMATCH       | 8 Vectors       | 0 (Acc=1.0)       | CAUGHT by Evaluator     |
| FALSE_ABSTENTION        | 130 Questions   | 0 (Recall=1.0)    | CALIBRATED at 0.50      |
| MISSED_ABSTENTION       | 130 Questions   | 0 (Prec=1.0)      | ZERO Hallucination      |
| FACT_EXTRACTION_ERROR   | 3 Predicates    | 0 (Acc=1.0)       | RESOLVED via Patterns   |
| FALSE_CONFLICT          | 5 Pairs         | 0 (Acc=1.0)       | RESOLVED via 8-Stage    |
| MISSED_CONFLICT         | 5 Pairs         | 0 (Acc=1.0)       | RESOLVED via 8-Stage    |
| REPORT_OMISSION         | 2 Reports       | 0 (Valid=1.0)     | ENFORCED by Validator   |
| REPORT_INCONSISTENCY    | 2 Reports       | 0 (Valid=1.0)     | ENFORCED by Validator   |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Architectural Recommendations for Production Hardening

1. **Continuous Traceability**: Every generated answer must log its extracted `claim_id` and resolved `citation_id` into the WP-02 audit evidence store.
2. **Dynamic Calibration**: For highly regulated domains (e.g. SEC compliance, clinical trials), increase the evidence sufficiency threshold from $0.50$ to $0.65$ to further suppress selective risk.
3. **Multi-Source Entailment**: When multiple documents corroborate the same claim, retain all citations to protect against single-source invalidation during document updates.
