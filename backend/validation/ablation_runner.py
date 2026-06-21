"""
Ablation Runner
================

Measures component contributions by disabling them and analyzing performance drops.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import AblationError


@dataclass
class AblationResult:
    """Result of an ablation study run for a component."""

    study_name: str
    ablated_component: str
    passed: bool
    full_accuracy: float
    ablated_accuracy: float
    impact_accuracy: float  # Δ_i = full_accuracy - ablated_accuracy
    full_latency_ms: float
    ablated_latency_ms: float
    impact_latency_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "study_name": self.study_name,
            "ablated_component": self.ablated_component,
            "passed": self.passed,
            "full_accuracy": round(self.full_accuracy, 4),
            "ablated_accuracy": round(self.ablated_accuracy, 4),
            "impact_accuracy": round(self.impact_accuracy, 4),
            "full_latency_ms": round(self.full_latency_ms, 2),
            "ablated_latency_ms": round(self.ablated_latency_ms, 2),
            "impact_latency_ms": round(self.impact_latency_ms, 2),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class AblationStudy:
    """Configuration for an ablation study."""

    name: str
    components: List[str]
    config_modifications: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class AblationRunner:
    """
    Run ablation studies on the pipeline to isolate component contributions.
    """

    def __init__(
        self,
        pipeline_fn: Callable,
        accuracy_fn: Optional[Callable[[Any, Any], float]] = None,
        min_impact_threshold: float = 0.0,
    ) -> None:
        """
        Parameters
        ----------
        pipeline_fn : Callable
            A pipeline function that accepts (input_data, disabled_components=None)
            and returns a result dict containing "answer", "tokens", etc.
        accuracy_fn : Optional[Callable]
            Evaluates accuracy between predicted answer and expected answer.
        min_impact_threshold : float
            Minimum expected degradation (drop in accuracy) to prove a component is useful.
        """
        self.pipeline_fn = pipeline_fn
        self.accuracy_fn = accuracy_fn or _default_accuracy
        self.min_impact_threshold = min_impact_threshold
        self.results: List[AblationResult] = []

    def run_study(
        self,
        study: AblationStudy,
        original_input: Any,
        expected_output: Any,
    ) -> List[AblationResult]:
        """
        Run the ablation study.
        """
        study_results = []
        
        # 1. Run full baseline pipeline (no ablated components)
        t0 = time.perf_counter()
        try:
            full_res = self.pipeline_fn(original_input, disabled_components=[])
            duration_full = (time.perf_counter() - t0) * 1000
            full_ans = full_res.get("answer", "")
            full_accuracy = self.accuracy_fn(full_res, expected_output)
        except Exception as exc:
            raise AblationError(f"Baseline run failed: {exc}")

        # 2. Run for each ablated component
        for component in study.components:
            t0 = time.perf_counter()
            passed = True
            error_message = None
            
            try:
                # Run the pipeline with the specified component disabled
                ablated_res = self.pipeline_fn(original_input, disabled_components=[component])
                duration_ablated = (time.perf_counter() - t0) * 1000
                
                ablated_ans = ablated_res.get("answer", "")
                ablated_accuracy = self.accuracy_fn(ablated_res, expected_output)
                
                impact_acc = full_accuracy - ablated_accuracy
                impact_lat = duration_full - duration_ablated
                
                # Check significance threshold if desired
                if self.min_impact_threshold > 0 and impact_acc < self.min_impact_threshold:
                    passed = False
                    error_message = (
                        f"Ablation drop {impact_acc:.4f} is below "
                        f"threshold {self.min_impact_threshold:.4f}"
                    )
                
                r = AblationResult(
                    study_name=study.name,
                    ablated_component=component,
                    passed=passed,
                    full_accuracy=full_accuracy,
                    ablated_accuracy=ablated_accuracy,
                    impact_accuracy=impact_acc,
                    full_latency_ms=duration_full,
                    ablated_latency_ms=duration_ablated,
                    impact_latency_ms=impact_lat,
                    error_message=error_message,
                    metadata={
                        "full_tokens": full_res.get("tokens", 0),
                        "ablated_tokens": ablated_res.get("tokens", 0),
                    }
                )
            except Exception as exc:
                duration_ablated = (time.perf_counter() - t0) * 1000
                r = AblationResult(
                    study_name=study.name,
                    ablated_component=component,
                    passed=False,
                    full_accuracy=full_accuracy,
                    ablated_accuracy=0.0,
                    impact_accuracy=full_accuracy,
                    full_latency_ms=duration_full,
                    ablated_latency_ms=duration_ablated,
                    impact_latency_ms=duration_full - duration_ablated,
                    error_message=str(exc),
                )
            
            study_results.append(r)
            self.results.append(r)
            
        return study_results


def _default_accuracy(predicted_res: Dict[str, Any], expected_res: Any) -> float:
    """Default accuracy calculator utilizing answer text token overlap."""
    pred_str = predicted_res.get("answer", "")
    
    if isinstance(expected_res, dict):
        exp_str = expected_res.get("expected_answer", "")
    elif isinstance(expected_res, str):
        exp_str = expected_res
    else:
        exp_str = str(expected_res)
        
    import re
    pred_tokens = set(re.findall(r"\w+", pred_str.lower()))
    exp_tokens = set(re.findall(r"\w+", exp_str.lower()))
    
    if not pred_tokens or not exp_tokens:
        return 0.0
        
    common = pred_tokens & exp_tokens
    p = len(common) / len(pred_tokens)
    r = len(common) / len(exp_tokens)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)
