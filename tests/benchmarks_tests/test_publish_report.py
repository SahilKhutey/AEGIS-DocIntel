"""Benchmark report rendering."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmarks.runners.publish_report import render




def test_render_includes_pipeline_names() -> None:
    md = render({
        "generated_at": "2026-06-30T00:00:00Z",
        "n_questions": 10,
        "aegis": {
            "retrieval": {"recall_at_1": 0.6, "recall_at_5": 0.8, "recall_at_10": 0.9,
                          "mrr": 0.7, "map": 0.65},
            "citations": {"citation_precision": 0.8, "citation_recall": 0.7,
                          "citation_ndcg": 0.75},
            "ragas":     {"faithfulness": 0.9, "answer_relevancy": 0.85,
                          "context_precision": 0.8, "context_recall": 0.7},
            "deepeval":  {"hallucination_rate": 0.05},
            "tokens":    {"reduction_p50_pct": 60.0, "reduction_p95_pct": 75.0,
                          "raw_p50": 1000, "aegis_p50": 400},
            "latency":   {"p50_ms": 120.0, "p95_ms": 230.0, "p99_ms": 280.0,
                          "mean_ms": 150.0},
            "engines":   {"contrib.results.dense": 0.8},
        },
        "vanilla": {
            "retrieval": {"recall_at_1": 0.3, "recall_at_5": 0.5, "recall_at_10": 0.6,
                          "mrr": 0.4, "map": 0.35},
            "citations": {"citation_precision": 0.4, "citation_recall": 0.5,
                          "citation_ndcg": 0.45},
            "ragas":     {"faithfulness": 0.6, "answer_relevancy": 0.55,
                          "context_precision": 0.5, "context_recall": 0.6},
            "deepeval":  {"hallucination_rate": 0.2},
            "tokens":    {"reduction_p50_pct": 0.0, "reduction_p95_pct": 0.0,
                          "raw_p50": 1000, "aegis_p50": 1000},
            "latency":   {"p50_ms": 200.0, "p95_ms": 400.0, "p99_ms": 500.0,
                          "mean_ms": 230.0},
        },
    })
    assert "AEGIS-DocIntel Benchmark Results" in md
    assert "Vanilla" in md and "Recall@5" in md
    assert "Faithfulness" in md
