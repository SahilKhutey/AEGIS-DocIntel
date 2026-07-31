# AEGIS Benchmark Suite

A reproducible evaluation harness for AEGIS-DocIntel. Produces numbers that
the README and `docs/Benchmarks.md` can claim honestly.

## Why this exists

Performance claims in the README were *projected* until now. This directory
contains the code that turns those claims into measured, versioned, CI-gated
numbers.

## What gets measured

| Category                  | Metric                                              | Source           |
| ------------------------- | --------------------------------------------------- | ---------------- |
| Retrieval quality         | Recall@K, MRR, MAP                                  | custom           |
| Answer quality            | Faithfulness, Answer Relevancy, Context Precision   | RAGAS            |
| Answer quality            | Hallucination, Toxicity, Bias                       | DeepEval         |
| Citation quality          | Citation Precision, Citation Recall, nDCG           | custom           |
| Compression               | Token reduction (raw → AEGIS export)                | custom           |
| Latency                   | p50/p95/p99 ingest + retrieval + generation         | custom           |
| Engine contribution       | Per-method weight share in fused result             | custom           |
| Pipeline comparison       | AEGIS vs. vanilla RAG (control)                     | both             |

## Quick start

```bash
# Run the full suite (writes JSON + Markdown)
python -m benchmarks.runners.run_all --questions benchmarks/golden/questions.jsonl --out benchmarks/results/latest.json

# View the published report
cat benchmarks/docs/Benchmarks.md
```

## CI regression gate

The workflow runs `python -m benchmarks.runners.run_regression`, which fails
if any metric regresses by more than its tolerance (configurable per metric)
vs. the last green baseline.
