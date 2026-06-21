"""
Robustness Test Runner
========================

Tests system behavior with noisy / adversarial / edge-case inputs.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .exceptions import RobustnessError


class Perturbation(Enum):
    """Types of input perturbations."""

    NOISE = "noise"
    DROPOUT = "dropout"
    SCRAMBLE = "scramble"
    TRUNCATE = "truncate"
    EMPTY = "empty"
    HUGE = "huge"
    SPECIAL_CHARS = "special_chars"
    UNICODE = "unicode"
    DUPLICATE = "duplicate"
    MIXED_LANGUAGES = "mixed_languages"


@dataclass
class RobustnessTestResult:
    """Result of robustness test."""

    perturbation: str
    num_trials: int
    success_rate: float
    avg_accuracy: float
    min_accuracy: float
    max_accuracy: float
    degradation: float  # vs unperturbed baseline
    per_trial: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "perturbation": self.perturbation,
            "num_trials": self.num_trials,
            "success_rate": round(self.success_rate, 4),
            "avg_accuracy": round(self.avg_accuracy, 4),
            "min_accuracy": round(self.min_accuracy, 4),
            "max_accuracy": round(self.max_accuracy, 4),
            "degradation": round(self.degradation, 4),
        }


class RobustnessTestRunner:
    """
    Test AMDI-OS robustness to noisy / adversarial inputs.
    """

    def __init__(
        self,
        accuracy_fn: Callable[[Any, Any], float],
        success_threshold: float = 0.5,
        num_trials: int = 10,
    ) -> None:
        self.accuracy_fn = accuracy_fn
        self.success_threshold = success_threshold
        self.num_trials = num_trials
        self.results: List[RobustnessTestResult] = []

    def run_robustness(
        self,
        pipeline_fn: Callable,
        original_input: Any,
        expected_output: Any,
        perturbation: Perturbation,
        perturbation_params: Optional[Dict[str, Any]] = None,
    ) -> RobustnessTestResult:
        """Run robustness test with given perturbation."""
        params = perturbation_params or {}
        accuracies: List[float] = []
        successes = 0
        errors: List[str] = []
        for trial in range(self.num_trials):
            try:
                perturbed = self._apply_perturbation(
                    original_input, perturbation, params, trial
                )
                output = pipeline_fn(perturbed)
                accuracy = self.accuracy_fn(output, expected_output)
                accuracies.append(accuracy)
                if accuracy >= self.success_threshold:
                    successes += 1
            except Exception as exc:
                errors.append(str(exc))
                accuracies.append(0.0)
        if not accuracies:
            return RobustnessTestResult(
                perturbation=perturbation.value,
                num_trials=self.num_trials,
                success_rate=0.0,
                avg_accuracy=0.0,
                min_accuracy=0.0,
                max_accuracy=0.0,
                degradation=1.0,
                errors=errors,
            )
        avg_acc = float(np.mean(accuracies))
        min_acc = float(np.min(accuracies))
        max_acc = float(np.max(accuracies))
        # baseline = expected vs itself = 1.0
        degradation = max(0.0, 1.0 - avg_acc)
        r = RobustnessTestResult(
            perturbation=perturbation.value,
            num_trials=self.num_trials,
            success_rate=successes / max(self.num_trials, 1),
            avg_accuracy=avg_acc,
            min_accuracy=min_acc,
            max_accuracy=max_acc,
            degradation=degradation,
            per_trial=accuracies,
            errors=errors,
        )
        self.results.append(r)
        return r

    def _apply_perturbation(
        self,
        data: Any,
        perturbation: Perturbation,
        params: Dict[str, Any],
        trial: int,
    ) -> Any:
        """Apply a perturbation to the input."""
        if perturbation == Perturbation.NOISE:
            return self._add_noise(data, params.get("level", 0.1))
        if perturbation == Perturbation.DROPOUT:
            return self._dropout(data, params.get("rate", 0.2))
        if perturbation == Perturbation.SCRAMBLE:
            return self._scramble(data)
        if perturbation == Perturbation.TRUNCATE:
            return self._truncate(data, params.get("fraction", 0.5))
        if perturbation == Perturbation.EMPTY:
            return "" if isinstance(data, str) else []
        if perturbation == Perturbation.HUGE:
            return self._make_huge(data, params.get("size", 10000))
        if perturbation == Perturbation.SPECIAL_CHARS:
            return self._add_special_chars(data)
        if perturbation == Perturbation.UNICODE:
            return self._add_unicode(data)
        if perturbation == Perturbation.DUPLICATE:
            return self._duplicate(data, params.get("copies", 3))
        if perturbation == Perturbation.MIXED_LANGUAGES:
            return self._add_mixed_languages(data)
        return data

    @staticmethod
    def _add_noise(data: Any, level: float) -> Any:
        if isinstance(data, str):
            chars = list(data)
            n_noise = max(1, int(len(chars) * level))
            for _ in range(n_noise):
                idx = random.randint(0, len(chars) - 1)
                chars[idx] = random.choice(string.ascii_letters)
            return "".join(chars)
        if isinstance(data, np.ndarray):
            noisy = data.copy()
            noise = np.random.randn(*data.shape) * level * np.abs(data).max()
            return noisy + noise
        return data

    @staticmethod
    def _dropout(data: Any, rate: float) -> Any:
        if isinstance(data, str):
            chars = list(data)
            n_drop = max(1, int(len(chars) * rate))
            for _ in range(n_drop):
                idx = random.randint(0, len(chars) - 1)
                chars[idx] = ""
            return "".join(c for c in chars if c)
        if isinstance(data, np.ndarray):
            mask = np.random.rand(*data.shape) > rate
            return data * mask
        return data

    @staticmethod
    def _scramble(data: Any) -> Any:
        if isinstance(data, str):
            words = data.split()
            random.shuffle(words)
            return " ".join(words)
        if isinstance(data, list):
            new_data = data.copy()
            random.shuffle(new_data)
            return new_data
        return data

    @staticmethod
    def _truncate(data: Any, fraction: float) -> Any:
        if isinstance(data, str):
            keep = int(len(data) * fraction)
            return data[:keep]
        if isinstance(data, list):
            keep = int(len(data) * fraction)
            return data[:keep]
        return data

    @staticmethod
    def _make_huge(data: Any, size: int) -> Any:
        if isinstance(data, str):
            return (data + " ") * (size // max(len(data), 1) + 1)
        return data

    @staticmethod
    def _add_special_chars(data: Any) -> Any:
        if isinstance(data, str):
            special = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
            return data + "".join(random.choices(special, k=20))
        return data

    @staticmethod
    def _add_unicode(data: Any) -> Any:
        if isinstance(data, str):
            return data + " " + " ".join(["日本語", "中文", "العربية", "Ελληνικά", "🔬⚛️🧬"])
        return data

    @staticmethod
    def _duplicate(data: Any, copies: int) -> Any:
        if isinstance(data, str):
            return data * copies
        if isinstance(data, list):
            return data * copies
        return data

    @staticmethod
    def _add_mixed_languages(data: Any) -> Any:
        if isinstance(data, str):
            return (
                data + " " + " ".join(["日本語", "中文", "العربية", "Ελληνικά", "🔬⚛️🧬"])
            )
        return data
