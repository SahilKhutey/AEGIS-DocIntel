# Benchmark Methodology

## Why both AEGIS and vanilla RAG

Every metric is reported *twice*: once for AEGIS and once for a vanilla
single-method RAG control. The control pins the floor; the delta is the
value AEGIS adds.

| Step | AEGIS | Vanilla |
| ---- | ----- | ------- |
| Ingest | Multilingual, layout-aware, structure-preserving | Naive chunk + retrieve |
| Retrieval | Hybrid 7-method + RRF + reranker | Cosine on bag-of-words |
| Context build | Token-budgeted exporter | First-K concatenation |
| Generation | Stub LLM (deterministic) | Stub LLM (deterministic) |

## Metrics in detail

### Retrieval
- **Recall@K** — fraction of gold units present in the top-K retrieved
- **MRR** — mean reciprocal rank of the first gold hit
- **MAP** — mean average precision (gold units can appear at any rank)

### Citations
- **Precision** — `(gold ∩ predicted) / predicted`
- **Recall** — `(gold ∩ predicted) / gold`
- **nDCG** — graded ranking of citations, gold set as relevance=1

### Generation (RAGAS)
- **Faithfulness** — claims in the answer are grounded in evidence
- **Answer Relevancy** — semantic match to question (or to ground truth proxy)
- **Context Precision / Recall** — evidence set quality

### Hallucination
- **DeepEval HallucinationMetric** when available
- **Unsupported-claim rate** (custom) as a deterministic fallback
- **Drop is good** for both

### Tokens
- **Raw** — total token count over the full source corpus
- **AEGIS** — total token count of evidence passed to the LLM
- **Reduction %** — `(raw − aegis) / raw × 100`

### Latency
- p50/p95/p99/mean over per-question total time
- Includes retrieval + generation under a stub LLM

## Reproducing

```bash
python -m benchmarks.golden.build_golden
python -m benchmarks.runners.run_all \
    --questions benchmarks/golden/questions.jsonl \
    --out benchmarks/results/latest.json
python -m benchmarks.runners.publish_report
```

The Markdown report lands at `benchmarks/docs/Benchmarks.md`.
A regression-gated CI job runs on every PR.
