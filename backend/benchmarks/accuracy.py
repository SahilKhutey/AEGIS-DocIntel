"""

Accuracy Benchmark

==================



Measures answer correctness via multiple methods:

- Exact match

- Token overlap (Jaccard)

- Semantic similarity (cosine)

- LLM-as-judge (optional)



Mathematical Foundation:

    Accuracy = (1/N) Σ 1[answer matches expected]



    where:

        exact_match       : exact string equality

        token_f1 ≥ 0.5    : token overlap sufficient

        semantic ≥ 0.8    : cosine similarity sufficient

"""



from __future__ import annotations



import re

from dataclasses import dataclass, field

from typing import Any, Callable, Dict, List, Optional



import numpy as np





@dataclass

class AccuracyResult:

    """Accuracy benchmark result."""



    total_questions: int

    correct: int

    accuracy: float

    method: str

    per_category: Dict[str, float] = field(default_factory=dict)

    per_difficulty: Dict[str, float] = field(default_factory=dict)

    per_question: List[Dict[str, Any]] = field(default_factory=list)



    def to_dict(self) -> dict:

        return {

            "total_questions": self.total_questions,

            "correct": self.correct,

            "accuracy": round(self.accuracy, 4),

            "method": self.method,

            "per_category": {k: round(v, 4) for k, v in self.per_category.items()},

            "per_difficulty": {k: round(v, 4) for k, v in self.per_difficulty.items()},

        }





class AccuracyBenchmark:

    """

    Accuracy benchmark with multiple matching strategies.

    """



    METHODS = ("exact", "token_f1", "semantic", "hybrid")



    def __init__(

        self,

        method: str = "hybrid",

        threshold: float = 0.5,

        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,

    ) -> None:

        if method not in self.METHODS:

            raise ValueError(f"Unknown method: {method}")

        self.method = method

        self.threshold = threshold

        self.embedding_fn = embedding_fn



    def evaluate(

        self,

        predictions: List[str],

        ground_truths: List["GroundTruthEntry"],

    ) -> AccuracyResult:

        """

        Evaluate accuracy of predictions against ground truth.

        """

        if len(predictions) != len(ground_truths):

            raise ValueError("predictions and ground_truths must have same length")

        per_q: List[Dict[str, Any]] = []

        correct = 0

        cat_correct: Dict[str, List[int]] = {}

        diff_correct: Dict[str, List[int]] = {}

        for pred, gt in zip(predictions, ground_truths):

            is_correct = self._is_correct(pred, gt.expected_answer)

            if is_correct:

                correct += 1

            # per category

            cat_correct.setdefault(gt.category, []).append(int(is_correct))

            # per difficulty

            diff_correct.setdefault(gt.difficulty, []).append(int(is_correct))

            per_q.append({

                "question": gt.question,

                "expected": gt.expected_answer,

                "predicted": pred,

                "correct": is_correct,

                "category": gt.category,

                "difficulty": gt.difficulty,

            })

        n = len(predictions)

        accuracy = correct / max(n, 1)

        per_cat = {k: float(np.mean(v)) for k, v in cat_correct.items()}

        per_diff = {k: float(np.mean(v)) for k, v in diff_correct.items()}

        return AccuracyResult(

            total_questions=n,

            correct=correct,

            accuracy=accuracy,

            method=self.method,

            per_category=per_cat,

            per_difficulty=per_diff,

            per_question=per_q,

        )



    def _is_correct(self, prediction: str, expected: str) -> bool:

        if self.method == "exact":

            return self._exact_match(prediction, expected)

        if self.method == "token_f1":

            return self._token_f1(prediction, expected) >= self.threshold

        if self.method == "semantic":

            return self._semantic_sim(prediction, expected) >= self.threshold

        # hybrid

        exact = self._exact_match(prediction, expected)

        if exact:

            return True

        token_f1 = self._token_f1(prediction, expected)

        semantic = (

            self._semantic_sim(prediction, expected)

            if self.embedding_fn is not None

            else 0.0

        )

        return token_f1 >= self.threshold or semantic >= 0.8



    @staticmethod

    def _exact_match(prediction: str, expected: str) -> bool:

        return _normalize(prediction) == _normalize(expected)



    @staticmethod

    def _token_f1(prediction: str, expected: str) -> float:

        pred_tokens = set(_tokenize(prediction))

        exp_tokens = set(_tokenize(expected))

        if not pred_tokens or not exp_tokens:

            return 0.0

        common = pred_tokens & exp_tokens

        precision = len(common) / len(pred_tokens)

        recall = len(common) / len(exp_tokens)

        if precision + recall == 0:

            return 0.0

        return 2 * precision * recall / (precision + recall)



    def _semantic_sim(self, prediction: str, expected: str) -> float:

        if self.embedding_fn is None:

            return 0.0

        try:

            v1 = self.embedding_fn(prediction)

            v2 = self.embedding_fn(expected)

            n1 = np.linalg.norm(v1)

            n2 = np.linalg.norm(v2)

            if n1 < 1e-12 or n2 < 1e-12:

                return 0.0

            return float(np.dot(v1, v2) / (n1 * n2))

        except Exception:

            return 0.0





def _normalize(text: str) -> str:

    return re.sub(r"\s+", " ", text.lower().strip())





def _tokenize(text: str) -> List[str]:

    return re.findall(r"\w+", text.lower())
