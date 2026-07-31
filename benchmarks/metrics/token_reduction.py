"""Token reduction (raw corpus -> AEGIS export)."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class TokenReduction:
    raw_total: int
    aegis_total: int
    ratio: float

    def to_dict(self) -> dict[str, float]:
        return {
            "raw_tokens": int(self.raw_total),
            "aegis_tokens": int(self.aegis_total),
            "reduction_pct": round(100 * (1 - self.aegis_total / max(self.raw_total, 1)), 2),
        }


def evaluate(per_query: list[tuple[int, int]]) -> TokenReduction:
    raw = sum(r for r, _ in per_query) if per_query else 0
    aeg = sum(a for _, a in per_query) if per_query else 0
    ratio = (aeg / max(raw, 1)) if per_query else 0.0
    return TokenReduction(
        raw_total=raw,
        aegis_total=aeg,
        ratio=ratio,
    )


def summarize(per_query: list[tuple[int, int]]) -> dict[str, float]:
    if not per_query:
        return {
            "raw_p50": 0.0, "raw_p95": 0.0,
            "aegis_p50": 0.0, "aegis_p95": 0.0,
            "reduction_p50_pct": 0.0, "reduction_p95_pct": 0.0,
        }
    raw = [r for r, _ in per_query]
    aeg = [a for _, a in per_query]
    med_raw = float(statistics.median(raw))
    med_aeg = float(statistics.median(aeg))
    p95_raw = float(_pct(raw, 95))
    p95_aeg = float(_pct(aeg, 95))

    return {
        "raw_p50": med_raw,
        "raw_p95": p95_raw,
        "aegis_p50": med_aeg,
        "aegis_p95": p95_aeg,
        "reduction_p50_pct": round(100 * (1 - med_aeg / max(med_raw, 1)), 2),
        "reduction_p95_pct": round(100 * (1 - p95_aeg / max(p95_raw, 1)), 2),
    }


def _pct(values, p: int) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return float(s[max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))] )


__all__ = ["evaluate", "summarize", "TokenReduction"]
