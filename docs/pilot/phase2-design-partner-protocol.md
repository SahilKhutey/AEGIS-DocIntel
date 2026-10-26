# AEGIS-DocIntel — Phase 2 External Design-Partner Protocol

> **Status Notice:** DRAFT PROTOCOL. No external pilots have been completed.
> In accordance with repository verification standards (see [README.md](../../README.md)), any future quantified result must link a public GitHub issue: [issues](https://github.com/SahilKhutey/AEGIS-DocIntel/issues/).

---

## 1. Objectives & Scope

The purpose of this design-partner protocol is to establish a standardized, transparent method for gathering qualitative and quantitative feedback from 3 to 5 external engineering teams prior to broad distribution.

AEGIS-DocIntel provides pre-LLM document structuring primitives:
- Deterministic PII redaction and secret sanitization
- Submodular knapsack context packing under constrained token budgets
- Spatial reading-order recovery for complex multi-column documents
- Source-grounded retrieval with citation integrity checking

This protocol ensures developer feedback is gathered rigorously without compromising security, privacy, or empirical truthfulness.

---

## 2. Eligibility & Partner Profile

We invite engineering teams who build LLM document pipelines to evaluate our core primitives.

### Target Profiles
1. **RAG Pipeline Engineers:** Teams processing complex multi-column PDFs, reports, or research documents.
2. **Enterprise AI Practitioners:** Developers handling sensitive transcripts requiring pre-prompt PII redaction.
3. **Context Optimization Engineers:** Teams requiring bounded prompt sizes with high informational coverage.

### Pre-Requisites
- Python 3.12 or 3.13 environment
- Familiarity with document ingestion APIs or RAG architectures
- Agreement to the privacy and synthetic-data guidelines below

---

## 3. Data Privacy & Explicit Consent

1. **Synthetic & Non-Confidential Data Only:**  
   Design partners must only process public, synthetic, or de-identified document corpora. No confidential, proprietary, or regulated production data should ever be submitted during evaluation trials.
2. **Self-Hosted Local Execution:**  
   The application runs entirely within the partner's local environment. Telemetry summaries do not export document content.
3. **Explicit Written Consent:**  
   Partners agree in writing that qualitative architectural feedback and non-confidential error traces may be referenced in public discussions.

---

## 4. Standard Evaluation Tasks

Each design partner executes a standard set of four tasks:

### Task A: Extraction Fidelity & Reading Order
- **Scenario:** Ingest a 2-column or 3-column document with headers, sidebars, and embedded tables.
- **Verification:** Evaluate whether the reconstructed text flow preserves natural reading order and whether tabular cells align with expected column bounds.

### Task B: Context Packing Under Strict Capacity
- **Scenario:** Pack multi-chunk retrieval results into strict prompt capacities (e.g., 2,000 to 8,000 capacity units).
- **Verification:** Verify that the context packer does not exceed the designated budget and maximizes topical diversity over redundant near-duplicates.

### Task C: Privacy & PII Scrubbing
- **Scenario:** Process transcripts containing synthetic names, email addresses, phone numbers, and placeholder API keys.
- **Verification:** Verify that sensitive entities are redacted before prompt compilation and that safe summary reports do not leak raw secrets.

### Task D: Grounding & Citation Validation
- **Scenario:** Submit domain questions against ingested documents.
- **Verification:** Confirm that answers cite genuine document chunk identifiers and that queries without evidence in the corpus are cleanly rejected.

---

## 5. Feedback Collection & Artifact Reporting

Partners provide structured feedback using the standardized JSON template (`artifacts/phase2/pilot-results-template.json`):

```json
{
  "partner_id": "partner-alpha",
  "evaluation_date": "2026-10-26",
  "environment": {
    "os": "Linux / Windows / macOS",
    "python_version": "3.12"
  },
  "task_feedback": {
    "task_a_extraction": {
      "rating": "satisfactory",
      "notes": "Linearization succeeded across 2-column layout."
    },
    "task_b_packing": {
      "rating": "satisfactory",
      "notes": "No budget overrun observed across tested prompts."
    },
    "task_c_privacy": {
      "rating": "satisfactory",
      "notes": "Targeted synthetic entities scrubbed correctly."
    },
    "task_d_citations": {
      "rating": "satisfactory",
      "notes": "All citations corresponded to retrieved IDs."
    }
  },
  "critical_defects_found": []
}
```

Partners submit results by opening a public issue on GitHub:
- Issue tracker: [https://github.com/SahilKhutey/AEGIS-DocIntel/issues/](https://github.com/SahilKhutey/AEGIS-DocIntel/issues/)
- Template: Design Partner Evaluation Feedback

---

## 6. Release Go / No-Go Decision Criteria

Before advancing from research MVP to broader availability, the following gates must be met:

1. **Zero Unhandled Server Exceptions:** Standard onboarding tasks execute without uncaught internal server errors.
2. **Automated Quality Benchmark Pass:** All benchmark gates pass deterministically in CI via `evaluation/scripts/run_all.py --fail-under-gates`.
3. **Verifiable Partner Reports:** At least 3 independent partner evaluation issues submitted with reproducible steps.
4. **Docs Verification Compliance:** All documentation statements continue to pass `scripts/check_docs_claims.py` checks.
