# 16 — Quality Feedback and Evaluation Loop

## 1. Purpose of the Feedback Loop

Human governance decisions generate irreplaceable supervised training data. To continuously improve automated fact extraction, chunking granularity, and citation accuracy, reviewers can capture granular diagnostic feedback via `QualityFeedbackForm`.

Endpoint: `POST /api/v1/reviews/{review_id}/feedback`

---

## 2. Issue Categories

1. **`wrong_value`**: The system identified the correct attribute, but extracted the wrong numeric value or date.
2. **`wrong_attribute`**: The extracted text was misclassified under the wrong entity schema attribute.
3. **`bad_evidence`**: The model produced a valid value, but cited an irrelevant or ungrounded passage.
4. **`hallucination`**: The statement has zero grounding in the source document.
5. **`missing_context`**: The value was extracted from a clause that was altered by a subsequent amendment or footnote.
6. **`other`**: General diagnostic observation.

---

## 3. Evaluation Dataset Generation

Feedback submissions are stored in the backend database and aggregated in `GovernanceMetrics.feedback_categories`. These metrics directly inform:
- Benchmark evaluation suites (`tests/benchmarks/`).
- Prompt engineering refinements for fact extraction pipelines.
- Vector chunking overlap adjustments.
