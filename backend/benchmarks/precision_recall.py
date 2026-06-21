"""

Precision, Recall, F1 Benchmark

================================



Standard IR metrics for retrieval and answer accuracy.



Mathematical Foundation:

    Precision = TP / (TP + FP)

    Recall    = TP / (TP + FN)

    F1        = 2 · P · R / (P + R)

    Fβ        = (1 + β²) · P · R / (β² · P + R)

    mAP       = mean Average Precision

    NDCG      = Normalized Discounted Cumulative Gain

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Set





@dataclass

class PrecisionRecallResult:

    """Precision/Recall benchmark result."""



    true_positives: int

    false_positives: int

    false_negatives: int

    precision: float

    recall: float

    f1: float

    f2: float = 0.0

    f05: float = 0.0

    support: int = 0

    per_category: Dict[str, Dict[str, float]] = field(default_factory=dict)

    per_question: List[Dict[str, Any]] = field(default_factory=list)



    def to_dict(self) -> dict:

        return {

            "true_positives": self.true_positives,

            "false_positives": self.false_positives,

            "false_negatives": self.false_negatives,

            "precision": round(self.precision, 4),

            "recall": round(self.recall, 4),

            "f1": round(self.f1, 4),

            "f2": round(self.f2, 4),

            "f05": round(self.f05, 4),

            "support": self.support,

            "per_category": self.per_category,

        }





@dataclass

class F1Result:

    """Detailed F1 analysis."""



    micro_f1: float

    macro_f1: float

    weighted_f1: float

    per_class: Dict[str, float] = field(default_factory=dict)

    confusion_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)



    def to_dict(self) -> dict:

        return {

            "micro_f1": round(self.micro_f1, 4),

            "macro_f1": round(self.macro_f1, 4),

            "weighted_f1": round(self.weighted_f1, 4),

            "per_class": {k: round(v, 4) for k, v in self.per_class.items()},

        }





class PrecisionRecallBenchmark:

    """Compute precision, recall, F1, F-beta metrics."""



    def __init__(self, beta: float = 1.0) -> None:

        self.beta = beta



    def evaluate(

        self,

        predicted_sets: List[Set[str]],

        expected_sets: List[Set[str]],

        categories: Optional[List[str]] = None,

    ) -> PrecisionRecallResult:

        """

        Evaluate precision/recall for a list of predictions.



        Parameters

        ----------

        predicted_sets : List[Set[str]]

            Each element is the set of items retrieved/predicted.

        expected_sets : List[Set[str]]

            Each element is the set of items expected (ground truth).

        categories : Optional[List[str]]

            Per-question category labels.

        """

        if len(predicted_sets) != len(expected_sets):

            raise ValueError("predicted_sets and expected_sets must have same length")

        total_tp = 0

        total_fp = 0

        total_fn = 0

        per_q: List[Dict[str, Any]] = []

        per_cat: Dict[str, Dict[str, int]] = {}

        for i, (pred, exp) in enumerate(zip(predicted_sets, expected_sets)):

            tp = len(pred & exp)

            fp = len(pred - exp)

            fn = len(exp - pred)

            total_tp += tp

            total_fp += fp

            total_fn += fn

            p = tp / max(len(pred), 1)

            r = tp / max(len(exp), 1)

            f1 = _safe_f1(p, r, self.beta)

            per_q.append({

                "index": i,

                "tp": tp,

                "fp": fp,

                "fn": fn,

                "precision": p,

                "recall": r,

                "f1": f1,

            })

            if categories is not None and i < len(categories):

                cat = categories[i]

                if cat not in per_cat:

                    per_cat[cat] = {"tp": 0, "fp": 0, "fn": 0}

                per_cat[cat]["tp"] += tp

                per_cat[cat]["fp"] += fp

                per_cat[cat]["fn"] += fn

        precision = total_tp / max(total_tp + total_fp, 1)

        recall = total_tp / max(total_tp + total_fn, 1)

        f1 = _safe_f1(precision, recall, self.beta)

        f2 = _safe_f1(precision, recall, 2.0)

        f05 = _safe_f1(precision, recall, 0.5)

        # per-category precision/recall

        per_cat_results: Dict[str, Dict[str, float]] = {}

        for cat, counts in per_cat.items():

            p = counts["tp"] / max(counts["tp"] + counts["fp"], 1)

            r = counts["tp"] / max(counts["tp"] + counts["fn"], 1)

            per_cat_results[cat] = {

                "precision": p,

                "recall": r,

                "f1": _safe_f1(p, r),

            }

        return PrecisionRecallResult(

            true_positives=total_tp,

            false_positives=total_fp,

            false_negatives=total_fn,

            precision=precision,

            recall=recall,

            f1=f1,

            f2=f2,

            f05=f05,

            support=len(predicted_sets),

            per_category=per_cat_results,

            per_question=per_q,

        )



    def evaluate_classification(

        self,

        y_true: List[str],

        y_pred: List[str],

    ) -> F1Result:

        """

        Compute micro/macro/weighted F1 for multi-class classification.



        Parameters

        ----------

        y_true : List[str]

        y_pred : List[str]

        """

        classes = sorted(set(y_true) | set(y_pred))

        # confusion matrix

        cm: Dict[str, Dict[str, int]] = {c: {p: 0 for p in classes} for c in classes}

        for t, p in zip(y_true, y_pred):

            if t in cm and p in cm[t]:

                cm[t][p] += 1

        # per-class F1

        per_class: Dict[str, float] = {}

        for c in classes:

            tp = cm[c][c]

            fp = sum(cm[other][c] for other in classes if other != c)

            fn = sum(cm[c][other] for other in classes if other != c)

            p = tp / max(tp + fp, 1)

            r = tp / max(tp + fn, 1)

            per_class[c] = _safe_f1(p, r)

        # micro

        total_tp = sum(cm[c][c] for c in classes)

        total_fp = sum(

            cm[other][c] for c in classes for other in classes if other != c

        )

        total_fn = sum(

            cm[c][other] for c in classes for other in classes if other != c

        )

        micro_p = total_tp / max(total_tp + total_fp, 1)

        micro_r = total_tp / max(total_tp + total_fn, 1)

        micro_f1 = _safe_f1(micro_p, micro_r)

        macro_f1 = (

            sum(per_class.values()) / max(len(per_class), 1)

        )

        # weighted

        weights = [sum(cm[c].values()) for c in classes]

        total = sum(weights)

        weighted_f1 = (

            sum(per_class[c] * w for c, w in zip(classes, weights)) / max(total, 1)

        )

        return F1Result(

            micro_f1=micro_f1,

            macro_f1=macro_f1,

            weighted_f1=weighted_f1,

            per_class=per_class,

            confusion_matrix=cm,

        )





def _safe_f1(precision: float, recall: float, beta: float = 1.0) -> float:

    """F-beta score with safety against division by zero."""

    if precision + recall == 0:

        return 0.0

    beta_sq = beta * beta

    return (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
