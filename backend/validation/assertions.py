"""
Custom assertions for AMDI-OS validation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np

from .exceptions import TestFailureError


class AMDIAssertions:
    """
    Custom assertions for AMDI-OS testing.
    """

    @staticmethod
    def assert_valid_output(
        output: Any,
        expected_keys: Optional[List[str]] = None,
        allow_none: bool = False,
    ) -> None:
        """Assert that an engine output has expected structure."""
        if output is None and not allow_none:
            raise TestFailureError("Output is None")
        if expected_keys and isinstance(output, dict):
            missing = [k for k in expected_keys if k not in output]
            if missing:
                raise TestFailureError(f"Missing keys: {missing}")

    @staticmethod
    def assert_within_tolerance(
        actual: float,
        expected: float,
        tolerance: float = 0.05,
        name: str = "value",
    ) -> None:
        """Assert actual is within `tolerance` of expected."""
        if expected == 0:
            if abs(actual) > tolerance:
                raise TestFailureError(
                    f"{name}: {actual} exceeds tolerance {tolerance}"
                )
            return
        diff = abs(actual - expected) / max(abs(expected), 1e-12)
        if diff > tolerance:
            raise TestFailureError(
                f"{name}: {actual} differs from {expected} by {diff:.4f} "
                f"(tolerance {tolerance})"
            )

    @staticmethod
    def assert_latency_below(
        latency_ms: float,
        threshold_ms: float,
        operation: str = "operation",
    ) -> None:
        if latency_ms > threshold_ms:
            raise TestFailureError(
                f"{operation} latency {latency_ms:.2f}ms exceeds "
                f"threshold {threshold_ms:.2f}ms"
            )

    @staticmethod
    def assert_memory_below(
        memory_mb: float,
        threshold_mb: float,
        component: str = "component",
    ) -> None:
        if memory_mb > threshold_mb:
            raise TestFailureError(
                f"{component} memory {memory_mb:.2f}MB exceeds "
                f"threshold {threshold_mb:.2f}MB"
            )

    @staticmethod
    def assert_token_within_budget(
        tokens: int,
        budget: int,
        operation: str = "operation",
    ) -> None:
        if tokens > budget:
            raise TestFailureError(
                f"{operation} used {tokens} tokens, exceeds budget {budget}"
            )

    @staticmethod
    def assert_accuracy_above(
        accuracy: float,
        threshold: float,
        operation: str = "operation",
    ) -> None:
        if accuracy < threshold:
            raise TestFailureError(
                f"{operation} accuracy {accuracy:.4f} below "
                f"threshold {threshold:.4f}"
            )

    @staticmethod
    def assert_f1_above(
        f1: float,
        threshold: float,
        operation: str = "operation",
    ) -> None:
        if f1 < threshold:
            raise TestFailureError(
                f"{operation} F1 {f1:.4f} below threshold {threshold:.4f}"
            )

    @staticmethod
    def assert_arrays_close(
        a: np.ndarray,
        b: np.ndarray,
        rtol: float = 1e-5,
        atol: float = 1e-8,
        name: str = "arrays",
    ) -> None:
        if a.shape != b.shape:
            raise TestFailureError(
                f"{name}: shape mismatch {a.shape} vs {b.shape}"
            )
        if not np.allclose(a, b, rtol=rtol, atol=atol):
            raise TestFailureError(f"{name}: values differ")

    @staticmethod
    def assert_conservation(
        input_val: float,
        output_val: float,
        compressed_val: float,
        discarded_val: float,
        tolerance: float = 0.01,
    ) -> None:
        """Assert information conservation law."""
        total = output_val + compressed_val + discarded_val
        diff = abs(input_val - total) / max(input_val, 1e-12)
        if diff > tolerance:
            raise TestFailureError(
                f"Conservation violated: {input_val} != {total} "
                f"(diff {diff:.4f})"
            )


def assert_valid_output(output: Any, expected_keys: Optional[List[str]] = None) -> None:
    AMDIAssertions.assert_valid_output(output, expected_keys)


def assert_within_tolerance(actual: float, expected: float, tolerance: float = 0.05) -> None:
    AMDIAssertions.assert_within_tolerance(actual, expected, tolerance)
