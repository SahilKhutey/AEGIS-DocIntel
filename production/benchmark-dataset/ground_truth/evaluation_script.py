"""
AMDI-OS Ground Truth Evaluation Script.

Evaluates system predictions against ground truth answers.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


def tokenize(text: str) -> List[str]:
    """Tokenize text into words."""
    return re.findall(r"\w+", text.lower())


def token_f1(predicted: str, expected: str) -> float:
    """Compute token-level F1 score."""
    pred_tokens = set(tokenize(predicted))
    exp_tokens = set(tokenize(expected))
    if not pred_tokens or not exp_tokens:
        return 0.0
    common = pred_tokens & exp_tokens
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(exp_tokens)
    return 2 * precision * recall / (precision + recall)


def page_recall(predicted_pages: List[int], expected_pages: List[int]) -> float:
    """Compute page recall."""
    if not expected_pages:
        return 1.0
    pred_set = set(predicted_pages)
    exp_set = set(expected_pages)
    return len(pred_set & exp_set) / len(exp_set)


def citation_recall(predicted_citations: List[str], expected_citations: List[str]) -> float:
    """Compute citation recall."""
    if not expected_citations:
        return 1.0
    pred_set = set(c.lower() for c in predicted_citations)
    exp_set = set(c.lower() for c in expected_citations)
    return len(pred_set & exp_set) / len(exp_set)


def evaluate_prediction(
    predicted_answer: str,
    predicted_pages: List[int],
    predicted_citations: List[str],
    ground_truth: Dict,
) -> Dict[str, float]:
    """
    Evaluate a single prediction against ground truth.
    """
    entry = ground_truth
    expected_answer = entry.get("expected_answer", "")
    expected_pages = entry.get("expected_pages", [])
    expected_citations = [
        f"{c.get('doc_id', '')}, p.{c.get('page', '?')}"
        for c in entry.get("expected_citations", [])
    ]

    answer_f1 = token_f1(predicted_answer, expected_answer)
    pg_recall = page_recall(predicted_pages, expected_pages)
    cit_recall = citation_recall(predicted_citations, expected_citations)

    # overall score: weighted combination
    overall = 0.6 * answer_f1 + 0.2 * pg_recall + 0.2 * cit_recall

    return {
        "answer_f1": answer_f1,
        "page_recall": pg_recall,
        "citation_recall": cit_recall,
        "overall": overall,
        "correct": overall >= 0.7,
    }


def evaluate_dataset(
    predictions: Dict[str, Dict],  # {doc_id: {question: {answer, pages, citations}}}
    ground_truth_file: str,
) -> Dict[str, float]:
    """
    Evaluate all predictions against a ground truth file.
    """
    with open(ground_truth_file, "r", encoding="utf-8") as f:
        gt = json.load(f)

    results = []
    # Support both flat and nested document key structure
    docs = gt.get("documents", gt)
    for doc_id, doc_gt in docs.items():
        if doc_id not in predictions:
            continue
        for entry in doc_gt.get("entries", []):
            question = entry.get("question", "")
            if question not in predictions[doc_id]:
                continue
            pred = predictions[doc_id][question]
            result = evaluate_prediction(
                pred.get("answer", ""),
                pred.get("pages", []),
                pred.get("citations", []),
                entry,
            )
            result["question"] = question
            result["doc_id"] = doc_id
            result["difficulty"] = entry.get("difficulty", "medium")
            results.append(result)

    if not results:
        return {"total": 0}

    # aggregate metrics
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total
    avg_answer_f1 = sum(r["answer_f1"] for r in results) / total
    avg_page_recall = sum(r["page_recall"] for r in results) / total
    avg_citation_recall = sum(r["citation_recall"] for r in results) / total

    # by difficulty
    by_difficulty = {}
    for diff in ["easy", "medium", "hard"]:
        diff_results = [r for r in results if r["difficulty"] == diff]
        if diff_results:
            by_difficulty[diff] = {
                "total": len(diff_results),
                "accuracy": sum(1 for r in diff_results if r["correct"]) / len(diff_results),
                "answer_f1": sum(r["answer_f1"] for r in diff_results) / len(diff_results),
            }

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "avg_answer_f1": avg_answer_f1,
        "avg_page_recall": avg_page_recall,
        "avg_citation_recall": avg_citation_recall,
        "by_difficulty": by_difficulty,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--output", default="evaluation.json")
    args = parser.parse_args()

    with open(args.predictions, "r") as f:
        predictions = json.load(f)
    results = evaluate_dataset(predictions, args.ground_truth)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))
