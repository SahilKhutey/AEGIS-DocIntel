"""
aegis.processing.benchmarking.metrics
=====================================
Quantitative metrics for OCR, text extraction, layout, reading order, and table accuracy.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


def levenshtein_distance(seq_a: Sequence[Any], seq_b: Sequence[Any]) -> Tuple[int, int, int, int]:
    """Calculate edit operations between two sequences using dynamic programming.
    
    Returns: (total_distance, substitutions, deletions, insertions)
    """
    n = len(seq_a)
    m = len(seq_b)

    # dp[i][j] stores (cost, subs, dels, ins)
    dp = [[(0, 0, 0, 0) for _ in range(m + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        dp[i][0] = (i, 0, i, 0)  # deletion from seq_a

    for j in range(1, m + 1):
        dp[0][j] = (j, 0, 0, j)  # insertion into seq_a

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # Sub: replace seq_a[i-1] with seq_b[j-1]
                sub_cost, subs, dels, ins = dp[i - 1][j - 1]
                cost_sub = (sub_cost + 1, subs + 1, dels, ins)

                # Del: delete seq_a[i-1]
                del_cost, subs, dels, ins = dp[i - 1][j]
                cost_del = (del_cost + 1, subs, dels + 1, ins)

                # Ins: insert seq_b[j-1]
                ins_cost, subs, dels, ins = dp[i][j - 1]
                cost_ins = (ins_cost + 1, subs, dels, ins + 1)

                best = min([cost_sub, cost_del, cost_ins], key=lambda x: x[0])
                dp[i][j] = best

    return dp[n][m]


class TextExtractionMetrics:
    """Calculates CER, WER, Word Accuracy, and Exact Match on text."""

    @staticmethod
    def calculate_cer(reference: str, hypothesis: str) -> Dict[str, Any]:
        """Calculate Character Error Rate (CER)."""
        ref_chars = list(reference)
        hyp_chars = list(hypothesis)
        n_ref = len(ref_chars)

        if n_ref == 0:
            cer = 0.0 if len(hyp_chars) == 0 else 1.0
            return {
                "cer": cer,
                "substitutions": 0,
                "deletions": 0,
                "insertions": len(hyp_chars),
                "reference_length": 0,
            }

        dist, subs, dels, ins = levenshtein_distance(ref_chars, hyp_chars)
        cer = dist / n_ref

        return {
            "cer": round(cer, 4),
            "substitutions": subs,
            "deletions": dels,
            "insertions": ins,
            "reference_length": n_ref,
        }

    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
        """Calculate Word Error Rate (WER) and Word Accuracy."""
        ref_words = re.findall(r"\S+", reference)
        hyp_words = re.findall(r"\S+", hypothesis)
        n_ref = len(ref_words)

        if n_ref == 0:
            wer = 0.0 if len(hyp_words) == 0 else 1.0
            return {
                "wer": wer,
                "word_accuracy": 1.0 - wer,
                "substitutions": 0,
                "deletions": 0,
                "insertions": len(hyp_words),
                "reference_word_count": 0,
            }

        dist, subs, dels, ins = levenshtein_distance(ref_words, hyp_words)
        wer = dist / n_ref
        accuracy = 1.0 - wer

        return {
            "wer": round(wer, 4),
            "word_accuracy": round(accuracy, 4),
            "substitutions": subs,
            "deletions": dels,
            "insertions": ins,
            "reference_word_count": n_ref,
        }

    @staticmethod
    def calculate_exact_match(
        predictions: List[str],
        ground_truths: List[str],
        normalize_whitespace: bool = True
    ) -> Dict[str, Any]:
        """Calculate Exact Match on structured text fields."""
        if not ground_truths or len(predictions) != len(ground_truths):
            return {"exact_match_ratio": 0.0, "total": 0, "correct": 0}

        correct = 0
        total = len(ground_truths)

        for p, gt in zip(predictions, ground_truths):
            p_clean = " ".join(p.split()) if normalize_whitespace else p
            gt_clean = " ".join(gt.split()) if normalize_whitespace else gt
            if p_clean == gt_clean:
                correct += 1

        ratio = correct / total if total > 0 else 0.0
        return {
            "exact_match_ratio": round(ratio, 4),
            "total": total,
            "correct": correct,
        }
