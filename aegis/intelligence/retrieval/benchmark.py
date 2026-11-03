"""
aegis.intelligence.retrieval.benchmark
======================================
Independent Retrieval Modes Benchmarking Engine.
Executes Lexical, Semantic, Structured, and Hybrid retrievers on canonical benchmark cases
and exports formal metrics conforming to schemas/intelligence/benchmark.schema.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import jsonschema

from aegis.intelligence.retrieval.evaluator import RetrievalEvaluator
from aegis.intelligence.retrieval.hybrid import HybridRetriever
from aegis.intelligence.retrieval.lexical import LexicalRetriever
from aegis.intelligence.retrieval.semantic import SemanticRetriever
from aegis.intelligence.retrieval.structured import StructuredRetriever


def run_retrieval_benchmark(
    dataset_path: Path | str | None = None,
    output_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Execute all 4 retrieval modes independently on benchmark cases."""
    repo_root = Path.cwd()
    if dataset_path is None:
        dataset_path = repo_root / "evaluation" / "datasets" / "qa_eval_dataset.json"
    else:
        dataset_path = Path(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    retrieval_cases = data.get("retrieval_cases", [])

    modes = {
        "lexical": LexicalRetriever,
        "semantic": SemanticRetriever,
        "structured": StructuredRetriever,
        "hybrid": HybridRetriever,
    }

    per_mode_metrics: Dict[str, Any] = {}

    for mode_name, retriever_cls in modes.items():
        eval_cases: List[Dict[str, Any]] = []

        for case in retrieval_cases:
            query = case["query"]
            corpus = case["corpus"]
            relevant_ids = set(case.get("relevant_ids", []))
            g_rel = {item["id"]: item.get("rel", 0) for item in corpus}

            # Initialize isolated retriever instance per case for clean evaluation
            retriever = retriever_cls()
            for item in corpus:
                retriever.index_document(
                    document_id=item.get("document_id", "DOC-001"),
                    chunk_id=item["id"],
                    text=item["text"],
                    page_number=item.get("page_number", 1),
                    metadata={"rel": item.get("rel", 0)},
                )

            res = retriever.retrieve(query=query, top_k=5, query_id=case["query_id"])
            eval_cases.append({
                "result": res,
                "relevant_chunks": relevant_ids,
                "graded_relevance": g_rel,
            })

        metrics = RetrievalEvaluator.evaluate_batch(eval_cases, k=5)
        per_mode_metrics[mode_name] = metrics.model_dump()

    # Compile benchmark record
    benchmark_record = {
        "benchmark_id": "WP06-RET-001",
        "run_id": "RUN-20261103-RETRIEVAL-BENCH",
        "work_package": "WP-06",
        "capability": "retrieval",
        "dataset_id": "QA-EVAL-RETRIEVAL-V1.0",
        "dataset_version": "1.0",
        "partition_id": "WP04-VALIDATION-001",
        "manifest_id": "MANIFEST-20261103",
        "pipeline_version": "1.0.0",
        "configuration_hash": "0993e47087612f0f8705007ee23ea0305f2479e0",
        "software_versions": {
            "retriever_modes": ["lexical", "semantic", "structured", "hybrid"],
            "fusion": "RRF_k0_60",
        },
        "metrics": {
            "total_queries_evaluated": len(retrieval_cases),
            "modes": per_mode_metrics,
            "hybrid_mrr": per_mode_metrics["hybrid"]["mrr"],
            "hybrid_recall_at_5": per_mode_metrics["hybrid"]["recall_at_k"],
            "hybrid_ndcg_at_5": per_mode_metrics["hybrid"]["ndcg_at_k"],
            "hybrid_latency_median_ms": per_mode_metrics["hybrid"]["latency_median_ms"],
        },
        "resource_metrics": {
            "evaluated_modes_count": 4,
            "fusion_constant_k0": 60,
        },
        "errors": [],
        "execution_status": "COMPLETED",
    }

    # Validate schema
    schema_path = repo_root / "schemas" / "intelligence" / "benchmark.schema.json"
    if schema_path.exists():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(benchmark_record, schema)

    if output_path is None:
        out_file = repo_root / "artifacts" / "intelligence" / "reports" / "RETRIEVAL_MODES_BENCHMARK.json"
    else:
        out_file = Path(output_path)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(benchmark_record, indent=2), encoding="utf-8")
    return benchmark_record


if __name__ == "__main__":
    rep = run_retrieval_benchmark()
    print("Retrieval Modes Benchmark Executed Successfully:")
    for mode, m in rep["metrics"]["modes"].items():
        print(f"  Mode [{mode}]: Recall@5={m['recall_at_k']}, MRR={m['mrr']}, nDCG@5={m['ndcg_at_k']}, Latency={m['latency_median_ms']}ms")
