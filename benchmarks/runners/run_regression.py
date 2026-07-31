"""CI regression gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TOLERANCES: dict[str, float] = {
    "recall_at_5":         -0.05,
    "mrr":                 -0.05,
    "map":                 -0.05,
    "citation_precision":  -0.05,
    "citation_recall":     -0.10,
    "faithfulness":        -0.05,
    "answer_relevancy":    -0.05,
    "hallucination_rate":   0.05,
    "reduction_p50_pct":   -10.0,
}


def _flat(metrics: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for group in ("retrieval", "citations", "ragas", "deepeval", "tokens"):
        for k, v in (metrics.get(group) or {}).items():
            if isinstance(v, (int, float)):
                out[k] = float(v)
    out.update(metrics.get("latency") or {})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True, type=Path)
    ap.add_argument("--baseline", required=True, type=Path)
    args = ap.parse_args()

    cur = json.loads(args.current.read_text(encoding="utf-8"))["aegis"]
    base = json.loads(args.baseline.read_text(encoding="utf-8"))["aegis"]
    cf = _flat(cur)
    bf = _flat(base)

    bad: list[str] = []
    summary: list[str] = []
    for metric, tol in TOLERANCES.items():
        if metric not in cf or metric not in bf:
            continue
        diff = cf[metric] - bf[metric]
        ok = diff >= tol
        summary.append(f"{'✓' if ok else '✗'} {metric:24s} {bf[metric]:.4f} -> {cf[metric]:.4f}  Δ={diff:+.4f}  tol={tol:+.4f}")
        if not ok:
            bad.append(metric)

    print("Regression vs. baseline")
    print("=" * 60)
    print("\n".join(summary))
    if bad:
        print("\nFAILED:", ", ".join(bad))
        return 1
    print("\nAll metrics within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
