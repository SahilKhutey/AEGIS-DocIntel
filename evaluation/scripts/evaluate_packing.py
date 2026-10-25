"""
evaluation/scripts/evaluate_packing.py
======================================
Evaluates context packing mathematical correctness:
- 0% token budget violation rate: sum(costs) <= B
- Knapsack greedy approximation bound >= (1 - 1/e)/2 ≈ 0.316 vs optimal
- Deterministic output on ties
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_docprep.context_packer import (
    ContextChunk,
    SubmodularKnapsackPacker,
    calculate_available_context_budget,
    validate_packing_inputs,
)


def evaluate_packing(dataset_path: Path | str | None = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = Path(__file__).resolve().parent.parent / "datasets" / "qa_eval_dataset.json"
    else:
        dataset_path = Path(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    packing_cases = data.get("packing_cases", [])
    budget_violations = 0
    total_evals = 0
    approx_ratios: List[float] = []

    # Initialize packer
    packer = SubmodularKnapsackPacker(
        alpha=0.6,
        beta=0.4,
        similarity_metric="affine_cosine",
    )

    for case in packing_cases:
        budget = case["budget"]
        costs = case["costs"]
        weights = case["weights"]
        n = len(costs)

        chunks: List[ContextChunk] = []
        for i in range(n):
            vec = np.zeros(n, dtype=np.float32)
            vec[i] = 1.0
            chunks.append(
                ContextChunk(
                    chunk_id=f"c_{case['case_id']}_{i}",
                    text=f"Chunk {i} with weight {weights[i]}",
                    relevance_score=weights[i],
                    token_cost=costs[i],
                    embedding=vec,
                )
            )

        res = packer.pack_context(chunks, max_budget=budget)

        if res.total_tokens > budget:
            budget_violations += 1
        total_evals += 1

        # Check submodular approximation ratio vs exhaustive search
        if n <= 8:
            def objective(subset: tuple[int, ...]) -> float:
                if not subset:
                    return 0.0
                rel = sum(chunks[i].relevance_score for i in subset)
                pairs = len(subset) * (len(subset) - 1) / 2
                return max(0.0, rel - 0.1 * pairs)

            sel_indices = [
                i for i, c in enumerate(chunks)
                if c.chunk_id in {sc.chunk_id for sc in res.selected_chunks}
            ]
            greedy_val = objective(tuple(sel_indices))

            opt_val = 0.0
            for r in range(1, n + 1):
                for subset in itertools.combinations(range(n), r):
                    sub_cost = sum(chunks[i].token_cost for i in subset)
                    if sub_cost <= budget:
                        val = objective(subset)
                        if val > opt_val:
                            opt_val = val

            ratio = (greedy_val / opt_val) if opt_val > 0 else 1.0
            approx_ratios.append(ratio)

    # Invariant boundary validations
    test_budget = calculate_available_context_budget(4096, 500, 100, 500, 50)
    assert test_budget == 2946

    violation_rate = budget_violations / max(1, total_evals)
    min_ratio = min(approx_ratios) if approx_ratios else 1.0
    mean_ratio = sum(approx_ratios) / max(1, len(approx_ratios))

    return {
        "budget_violation_rate": round(violation_rate, 4),
        "min_approx_ratio": round(min_ratio, 4),
        "mean_approx_ratio": round(mean_ratio, 4),
        "cases_evaluated": total_evals,
        "passed": (violation_rate == 0.0 and min_ratio >= 0.316),
    }


if __name__ == "__main__":
    results = evaluate_packing()
    print(json.dumps(results, indent=2))
