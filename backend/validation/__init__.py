"""
AMDI-OS Validation Framework
=============================

Comprehensive validation across 6 test categories:
    - Unit Tests         : individual component correctness
    - Integration Tests  : component interaction
    - End-to-End Tests   : full pipeline flow
    - Stress Tests       : load / scalability
    - Robustness Tests   : noisy inputs, edge cases
    - Ablation Tests     : engine contribution analysis

Mathematical Foundation:
    Test coverage:
        C = (T_passing / T_total) · 100

    Robustness score:
        R = (1/N) Σ performance(perturbed_input_i)

    Ablation impact:
        Δ_i = performance_full - performance_without_engine_i

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .validation_engine import (
    ValidationEngine,
    ValidationSuite,
    ValidationResult,
)
from .unit_test_runner import UnitTestRunner, UnitTestResult
from .integration_test_runner import (
    IntegrationTestRunner,
    IntegrationTestResult,
)
from .e2e_test_runner import E2ETestRunner, E2ETestResult
from .stress_test_runner import (
    StressTestRunner,
    StressTestResult,
    LoadProfile,
)
from .robustness_test_runner import (
    RobustnessTestRunner,
    RobustnessTestResult,
    Perturbation,
)
from .ablation_runner import (
    AblationRunner,
    AblationResult,
    AblationStudy,
)
from .validation_report import (
    ValidationReport,
    ValidationMetrics,
)
from .assertions import (
    AMDIAssertions,
    assert_valid_output,
    assert_within_tolerance,
)
from .fixtures import (
    sample_document,
    sample_pdf_text,
    sample_ground_truth,
)
from .exceptions import (
    ValidationError,
    TestFailureError,
    CoverageThresholdError,
)

__all__ = [
    "ValidationEngine",
    "ValidationSuite",
    "ValidationResult",
    "UnitTestRunner",
    "UnitTestResult",
    "IntegrationTestRunner",
    "IntegrationTestResult",
    "E2ETestRunner",
    "E2ETestResult",
    "StressTestRunner",
    "StressTestResult",
    "LoadProfile",
    "RobustnessTestRunner",
    "RobustnessTestResult",
    "Perturbation",
    "AblationRunner",
    "AblationResult",
    "AblationStudy",
    "ValidationReport",
    "ValidationMetrics",
    "AMDIAssertions",
    "assert_valid_output",
    "assert_within_tolerance",
    "sample_document",
    "sample_pdf_text",
    "sample_ground_truth",
    "ValidationError",
    "TestFailureError",
    "CoverageThresholdError",
]

__version__ = "1.0.0"
