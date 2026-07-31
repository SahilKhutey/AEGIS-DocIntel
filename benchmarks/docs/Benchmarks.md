# AEGIS-DocIntel Benchmark Results

_Generated: 2026-07-31T03:25:55.549128+00:00 · N = 10 questions_

> Numbers below are **measured**, not projected. Sources: AEGIS pipeline vs.
> vanilla RAG control. Re-run with `python -m benchmarks.runners.run_all`.

## Retrieval quality (higher is better)

| Metric          | AEGIS | Vanilla |
| --------------- | ----- | ------- |
| Recall@1        | 0.7000 | 0.6000 |
| Recall@5        | 0.9000 | 0.7500 |
| Recall@10       | 0.9000 | 0.7500 |
| MRR             | 0.8250 | 0.6750 |
| MAP             | 0.7950 | 0.6500 |

## Citation quality (higher is better)

| Metric            | AEGIS | Vanilla |
| ----------------- | ----- | ------- |
| Citation Precision | 0.0426 | 0.0408 |
| Citation Recall    | 0.2000 | 0.2000 |
| Citation nDCG      | 0.5897 | 0.2000 |

## Answer quality (RAGAS — higher better, except hallucination)

| Metric             | AEGIS | Vanilla |
| ------------------ | ----- | ------- |
| Faithfulness        | 0.1000 | 0.6000 |
| Answer Relevancy    | 0.0067 | 0.1012 |
| Context Precision   | 0.0000 | 0.0000 |
| Context Recall      | 0.0000 | 0.0000 |
| Hallucination rate  | 1.0000 | 0.6000 |

## Token compression

| Metric                     | AEGIS | Vanilla |
| -------------------------- | ----- | ------- |
| Reduction p50 (%)            | 71.79 | 65.72 |
| Reduction p95 (%)            | 72.12 | 54.12 |
| Raw tokens (sum)             | 237.5 | 194.0 |
| AEGIS tokens (sum)           | 67.0 | 66.5 |

## Latency (ms — lower better)

| Metric | AEGIS | Vanilla |
| ------ | ----- | ------- |
| p50     | 19.609 | 0.500 |
| p95     | 19670.577 | 0.500 |
| p99     | 19670.577 | 0.500 |
| mean    | 1984.715 | 0.500 |

## Engine contributions (AEGIS)

| Counter | Value |
| --- | --- |
| `latency_share_ms.retrieval_ms` | 19847.075 |
| `latency_share_ms.generation_ms` | 0.073 |

## Methodology

See `benchmarks/docs/benchmark_methodology.md`.
