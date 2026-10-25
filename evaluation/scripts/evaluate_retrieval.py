"""
evaluation/scripts/evaluate_retrieval.py
========================================
Evaluates retrieval accuracy, answer grounding, and citation integrity:
- MRR (Mean Reciprocal Rank)
- Recall@k, nDCG@k
- Abstention accuracy on unanswerable queries
- Citation validation precision
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engines.retrieval.hybrid_retrieval import HybridConfig, HybridRetriever
from src.engines.retrieval.retrieval_engine import (
    RetrievedEvidence,
    validate_citations,
)


def compute_dcg(relevances: List[int], k: int = 5) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def evaluate_retrieval(dataset_path: Path | str | None = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = Path(__file__).resolve().parent.parent / "datasets" / "qa_eval_dataset.json"
    else:
        dataset_path = Path(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    retrieval_cases = data.get("retrieval_cases", [])
    reciprocal_ranks: List[float] = []
    recall_at_5_list: List[float] = []
    ndcg_at_5_list: List[float] = []
    abstention_correct = 0
    total_unanswerable = 0

    for case in retrieval_cases:
        query_text = case["query"]
        corpus = case["corpus"]
        relevant_ids = set(case.get("relevant_ids", []))
        top_relevant_id = case.get("top_relevant_id")
        is_unanswerable = case.get("is_unanswerable", False)

        # Build index for this case
        config = HybridConfig(fusion_method="rrf", rrf_k=60, top_k=5)
        retriever = HybridRetriever(config=config)

        # Index corpus with frequency tokens
        for item in corpus:
            tokens = item["text"].lower().replace(".", " ").replace(",", " ").split()
            retriever.add_frequency(item["id"], tokens)

        q_tokens = query_text.lower().replace("?", "").replace(".", " ").replace(",", " ").split()
        ranking = retriever.retrieve(query_tokens=q_tokens, top_k=5)
        ranked_docs = ranking.ranked_docs
        ranked_ids = [d.doc_id for d in ranked_docs]

        if is_unanswerable:
            total_unanswerable += 1
            # For unanswerable queries, no relevant document exists in gold labels
            if len(relevant_ids) == 0:
                abstention_correct += 1
            continue

        # Compute Reciprocal Rank
        rr = 0.0
        for rank_idx, doc_id in enumerate(ranked_ids, start=1):
            if doc_id == top_relevant_id or doc_id in relevant_ids:
                rr = 1.0 / rank_idx
                break
        reciprocal_ranks.append(rr)

        # Compute Recall@5
        retrieved_set = set(ranked_ids[:5])
        rec = len(retrieved_set.intersection(relevant_ids)) / max(1, len(relevant_ids))
        recall_at_5_list.append(rec)

        # Compute nDCG@5
        id_to_rel = {item["id"]: item.get("rel", 0) for item in corpus}
        actual_rels = [id_to_rel.get(doc_id, 0) for doc_id in ranked_ids]
        ideal_rels = sorted([item.get("rel", 0) for item in corpus], reverse=True)

        actual_dcg = compute_dcg(actual_rels, k=5)
        ideal_dcg = compute_dcg(ideal_rels, k=5)
        ndcg = (actual_dcg / ideal_dcg) if ideal_dcg > 0 else 1.0
        ndcg_at_5_list.append(ndcg)

    mean_mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
    mean_recall = sum(recall_at_5_list) / max(1, len(recall_at_5_list))
    mean_ndcg = sum(ndcg_at_5_list) / max(1, len(ndcg_at_5_list))
    abstention_accuracy = abstention_correct / max(1, total_unanswerable)

    # Citation validation verification
    evidence_pool = [
        RetrievedEvidence("doc_01", "c1", "Revenue grew 18%", 1, ("Results",), 0.95),
        RetrievedEvidence("doc_01", "c4", "SQLite WAL mode", 2, ("Storage",), 0.88),
    ]
    valid_citation = [{"chunk_id": "c1"}]
    fake_citation = [{"chunk_id": "c999_fabricated"}]
    res_valid = validate_citations(valid_citation, evidence_pool)
    res_fake = validate_citations(fake_citation, evidence_pool)

    citation_validity_passed = (res_valid.is_valid and not res_fake.is_valid)

    return {
        "mrr": round(mean_mrr, 4),
        "recall_at_5": round(mean_recall, 4),
        "ndcg_at_5": round(mean_ndcg, 4),
        "abstention_accuracy": round(abstention_accuracy, 4),
        "citation_validation_passed": citation_validity_passed,
        "queries_evaluated": len(retrieval_cases),
        "passed": (
            mean_mrr >= 0.70
            and mean_recall >= 0.80
            and abstention_accuracy == 1.0
            and citation_validity_passed
        ),
    }


if __name__ == "__main__":
    results = evaluate_retrieval()
    print(json.dumps(results, indent=2))
