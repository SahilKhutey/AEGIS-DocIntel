"""Render JSON results into a Markdown report."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


TEMPLATE = """# AEGIS-DocIntel Benchmark Results

_Generated: {ts} · N = {n} questions_

> Numbers below are **measured**, not projected. Sources: AEGIS pipeline vs.
> vanilla RAG control. Re-run with `python -m benchmarks.runners.run_all`.

## Retrieval quality (higher is better)

| Metric          | AEGIS | Vanilla |
| --------------- | ----- | ------- |
| Recall@1        | {aegis_recall_at_1:.4f} | {vanilla_recall_at_1:.4f} |
| Recall@5        | {aegis_recall_at_5:.4f} | {vanilla_recall_at_5:.4f} |
| Recall@10       | {aegis_recall_at_10:.4f} | {vanilla_recall_at_10:.4f} |
| MRR             | {aegis_mrr:.4f} | {vanilla_mrr:.4f} |
| MAP             | {aegis_map:.4f} | {vanilla_map:.4f} |

## Citation quality (higher is better)

| Metric            | AEGIS | Vanilla |
| ----------------- | ----- | ------- |
| Citation Precision | {aegis_cp:.4f} | {vanilla_cp:.4f} |
| Citation Recall    | {aegis_cr:.4f} | {vanilla_cr:.4f} |
| Citation nDCG      | {aegis_ndcg:.4f} | {vanilla_ndcg:.4f} |

## Answer quality (RAGAS — higher better, except hallucination)

| Metric             | AEGIS | Vanilla |
| ------------------ | ----- | ------- |
| Faithfulness        | {aegis_faith:.4f} | {vanilla_faith:.4f} |
| Answer Relevancy    | {aegis_rel:.4f} | {vanilla_rel:.4f} |
| Context Precision   | {aegis_cp2:.4f} | {vanilla_cp2:.4f} |
| Context Recall      | {aegis_cr2:.4f} | {vanilla_cr2:.4f} |
| Hallucination rate  | {aegis_hallu:.4f} | {vanilla_hallu:.4f} |

## Token compression

| Metric                     | AEGIS | Vanilla |
| -------------------------- | ----- | ------- |
| Reduction p50 (%)            | {aegis_rp50:.2f} | {vanilla_rp50:.2f} |
| Reduction p95 (%)            | {aegis_rp95:.2f} | {vanilla_rp95:.2f} |
| Raw tokens (sum)             | {aegis_raw_sum} | {vanilla_raw_sum} |
| AEGIS tokens (sum)           | {aegis_sum} | {vanilla_sum} |

## Latency (ms — lower better)

| Metric | AEGIS | Vanilla |
| ------ | ----- | ------- |
| p50     | {aegis_p50:.3f} | {vanilla_p50:.3f} |
| p95     | {aegis_p95:.3f} | {vanilla_p95:.3f} |
| p99     | {aegis_p99:.3f} | {vanilla_p99:.3f} |
| mean    | {aegis_mean:.3f} | {vanilla_mean:.3f} |

## Engine contributions (AEGIS)

| Counter | Value |
| --- | --- |
{engine_rows}

## Methodology

See `benchmarks/docs/benchmark_methodology.md`.
"""


def render(data: dict) -> str:
    a = data["aegis"]; v = data["vanilla"]
    ar = a["retrieval"]; vr = v["retrieval"]
    ac = a["citations"]; vc = v["citations"]
    araga = a["ragas"]; vraga = v["ragas"]
    adee = a["deepeval"]; vdee = v["deepeval"]
    atok = a["tokens"]; vtok = v["tokens"]
    alat = a["latency"]; vlat = v["latency"]
    eng = a.get("engines", {})

    rows = "\n".join(f"| `{k}` | {val} |" for k, val in eng.items()) or "| — | — |"

    return TEMPLATE.format(
        ts=data.get("generated_at", ""), n=data.get("n_questions", 0),
        aegis_recall_at_1=ar.get("recall_at_1", 0),
        vanilla_recall_at_1=vr.get("recall_at_1", 0),
        aegis_recall_at_5=ar.get("recall_at_5", 0),
        vanilla_recall_at_5=vr.get("recall_at_5", 0),
        aegis_recall_at_10=ar.get("recall_at_10", 0),
        vanilla_recall_at_10=vr.get("recall_at_10", 0),
        aegis_mrr=ar.get("mrr", 0), vanilla_mrr=vr.get("mrr", 0),
        aegis_map=ar.get("map", 0), vanilla_map=vr.get("map", 0),
        aegis_cp=ac.get("citation_precision", 0),
        vanilla_cp=vc.get("citation_precision", 0),
        aegis_cr=ac.get("citation_recall", 0),
        vanilla_cr=vc.get("citation_recall", 0),
        aegis_ndcg=ac.get("citation_ndcg", 0),
        vanilla_ndcg=vc.get("citation_ndcg", 0),
        aegis_faith=araga.get("faithfulness", 0), vanilla_faith=vraga.get("faithfulness", 0),
        aegis_rel=araga.get("answer_relevancy", 0), vanilla_rel=vraga.get("answer_relevancy", 0),
        aegis_cp2=araga.get("context_precision", 0), vanilla_cp2=vraga.get("context_precision", 0),
        aegis_cr2=araga.get("context_recall", 0), vanilla_cr2=vraga.get("context_recall", 0),
        aegis_hallu=adee.get("hallucination_rate", 0),
        vanilla_hallu=vdee.get("hallucination_rate", 0),
        aegis_rp50=atok.get("reduction_p50_pct", 0), vanilla_rp50=vtok.get("reduction_p50_pct", 0),
        aegis_rp95=atok.get("reduction_p95_pct", 0), vanilla_rp95=vtok.get("reduction_p95_pct", 0),
        aegis_raw_sum=atok.get("raw_p50", 0), vanilla_raw_sum=vtok.get("raw_p50", 0),
        aegis_sum=atok.get("aegis_p50", 0), vanilla_sum=vtok.get("aegis_p50", 0),
        aegis_p50=alat.get("p50_ms", 0), vanilla_p50=vlat.get("p50_ms", 0),
        aegis_p95=alat.get("p95_ms", 0), vanilla_p95=vlat.get("p95_ms", 0),
        aegis_p99=alat.get("p99_ms", 0), vanilla_p99=vlat.get("p99_ms", 0),
        aegis_mean=alat.get("mean_ms", 0), vanilla_mean=vlat.get("mean_ms", 0),
        engine_rows=rows,
    )


__all__ = ["render"]
