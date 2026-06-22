"""
A/B Tester
============

A/B testing framework for weight variants and strategy configurations.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ABTestStatus(Enum):
    """A/B test status."""

    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ABTestVariant:
    """A single variant in an A/B test."""

    variant_id: str
    name: str
    config: Dict[str, Any]
    weight: float = 1.0  # traffic allocation weight
    impressions: int = 0
    conversions: int = 0
    sum_metric: float = 0.0
    sum_sq_metric: float = 0.0

    @property
    def conversion_rate(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.conversions / self.impressions

    @property
    def mean_metric(self) -> float:
        if self.impressions == 0:
            return 0.0
        return self.sum_metric / self.impressions

    @property
    def variance(self) -> float:
        if self.impressions < 2:
            return 0.0
        mean = self.mean_metric
        return max(0, (self.sum_sq_metric / self.impressions) - mean ** 2)

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


@dataclass
class ABTestResult:
    """Result of an A/B test."""

    test_id: str
    test_name: str
    status: ABTestStatus
    variants: Dict[str, ABTestVariant]
    winner: Optional[str]
    confidence: float
    lift: float
    p_value: float
    start_time: float
    end_time: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "variants": {
                vid: {
                    "name": v.name,
                    "impressions": v.impressions,
                    "conversions": v.conversions,
                    "mean_metric": v.mean_metric,
                    "conversion_rate": v.conversion_rate,
                }
                for vid, v in self.variants.items()
            },
            "winner": self.winner,
            "confidence": self.confidence,
            "lift": self.lift,
            "p_value": self.p_value,
        }


@dataclass
class ABTest:
    """An A/B test."""

    test_id: str
    test_name: str
    description: str
    variants: Dict[str, ABTestVariant]
    status: ABTestStatus = ABTestStatus.DRAFT
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metric_name: str = "accuracy"
    min_sample_size: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTester:
    """
    A/B testing framework for comparing weight variants.
    """

    def __init__(self) -> None:
        self.tests: Dict[str, ABTest] = {}

    def create_test(
        self,
        test_name: str,
        variants_config: List[Dict[str, Any]],
        description: str = "",
        metric_name: str = "accuracy",
        min_sample_size: int = 100,
    ) -> ABTest:
        """Create a new A/B test."""
        test_id = f"abtest_{int(time.time() * 1000)}"
        variants = {}
        for v_config in variants_config:
            vid = v_config.get("variant_id", f"v_{len(variants)}")
            variants[vid] = ABTestVariant(
                variant_id=vid,
                name=v_config.get("name", vid),
                config=v_config.get("config", {}),
                weight=v_config.get("weight", 1.0 / len(variants_config)),
            )
        test = ABTest(
            test_id=test_id,
            test_name=test_name,
            description=description,
            variants=variants,
            metric_name=metric_name,
            min_sample_size=min_sample_size,
        )
        self.tests[test_id] = test
        return test

    def start_test(self, test_id: str) -> None:
        """Start a test."""
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        test = self.tests[test_id]
        test.status = ABTestStatus.RUNNING
        test.start_time = time.time()

    def pause_test(self, test_id: str) -> None:
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        self.tests[test_id].status = ABTestStatus.PAUSED

    def assign_variant(self, test_id: str, user_id: str) -> str:
        """Assign a user to a variant (deterministic by user_id hash)."""
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        test = self.tests[test_id]
        if test.status != ABTestStatus.RUNNING:
            raise ValueError(f"Test {test_id} is not running")
        # hash-based assignment for consistency
        hash_val = hash((test_id, user_id)) % (10 ** 8)
        total_weight = sum(v.weight for v in test.variants.values())
        cum_weight = 0.0
        for variant_id, variant in test.variants.items():
            cum_weight += variant.weight / total_weight
            if hash_val / (10 ** 8) < cum_weight:
                return variant_id
        return list(test.variants.keys())[0]

    def record_impression(self, test_id: str, variant_id: str) -> None:
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        if variant_id not in self.tests[test_id].variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        self.tests[test_id].variants[variant_id].impressions += 1

    def record_metric(
        self,
        test_id: str,
        variant_id: str,
        metric_value: float,
        converted: bool = False,
    ) -> None:
        """Record a metric observation."""
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        variant = self.tests[test_id].variants[variant_id]
        variant.sum_metric += metric_value
        variant.sum_sq_metric += metric_value ** 2
        if converted:
            variant.conversions += 1

    def analyze(self, test_id: str) -> ABTestResult:
        """Analyze A/B test results with statistical significance."""
        if test_id not in self.tests:
            raise ValueError(f"Unknown test: {test_id}")
        test = self.tests[test_id]
        # find best variant by mean metric
        best_variant_id = max(
            test.variants,
            key=lambda vid: test.variants[vid].mean_metric,
        )
        # compute p-value using two-sample t-test
        variant_ids = list(test.variants.keys())
        if len(variant_ids) >= 2:
            control_id = variant_ids[0]
            treatment_id = best_variant_id
            p_value = self._two_sample_ttest(
                self.tests[test_id].variants[control_id],
                self.tests[test_id].variants[treatment_id],
            )
        else:
            p_value = 1.0
        control_mean = test.variants[variant_ids[0]].mean_metric
        best_mean = test.variants[best_variant_id].mean_metric
        lift = (
            (best_mean - control_mean) / control_mean
            if control_mean > 0 else 0.0
        )
        confidence = 1.0 - p_value
        return ABTestResult(
            test_id=test_id,
            test_name=test.test_name,
            status=test.status,
            variants=test.variants,
            winner=best_variant_id,
            confidence=confidence,
            lift=lift,
            p_value=p_value,
            start_time=test.start_time or 0.0,
            end_time=test.end_time,
            metadata=test.metadata,
        )

    def _two_sample_ttest(
        self,
        control,
        treatment,
    ) -> float:
        """Compute two-sample t-test p-value."""
        n1 = control.impressions
        n2 = treatment.impressions
        if n1 < 2 or n2 < 2:
            return 1.0
        m1 = control.mean_metric
        m2 = treatment.mean_metric
        v1 = control.variance
        v2 = treatment.variance
        # pooled variance
        pooled_var = ((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2)
        if pooled_var <= 0:
            if m1 != m2:
                pooled_var = 1e-9
            else:
                return 1.0
        se = math.sqrt(pooled_var * (1/n1 + 1/n2))
        if se == 0:
            return 1.0
        t_stat = (m2 - m1) / se
        # approximate two-tailed p-value using normal distribution
        p = 2 * (1 - _normal_cdf(abs(t_stat)))
        return min(max(p, 0.0), 1.0)

    def complete_test(self, test_id: str) -> ABTestResult:
        """Complete a test and return final results."""
        test = self.tests[test_id]
        test.status = ABTestStatus.COMPLETED
        test.end_time = time.time()
        return self.analyze(test_id)

    def list_tests(self) -> List[ABTest]:
        return list(self.tests.values())


def _normal_cdf(x: float) -> float:
    """Standard normal CDF using error function approximation."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
