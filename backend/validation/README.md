# AMDI-OS Validation Framework

Comprehensive, production-grade validation suite across six test levels.

## Directory Structure

```
backend/validation/
├── __init__.py
├── validation_engine.py         # Main orchestrator
├── unit_test_runner.py          # Unit test runner
├── integration_test_runner.py   # Integration test runner
├── e2e_test_runner.py           # End-to-end test runner
├── stress_test_runner.py        # Stress test runner
├── robustness_test_runner.py    # Robustness test runner
├── ablation_runner.py           # Ablation study runner
├── validation_report.py         # Report data structures
├── assertions.py                # Custom assertions
├── fixtures.py                  # Test fixtures
├── exceptions.py                # Custom exceptions
└── README.md
```

## Mathematical Foundation

### 1. Test Coverage
$$C = \frac{T_{\text{passing}}}{T_{\text{total}}} \times 100$$
Where:
- $C$ is the overall pass rate coverage percentage.
- $T_{\text{passing}}$ is the number of passing unit, integration, and E2E checks.
- $T_{\text{total}}$ is the total number of tests executed.

### 2. Robustness Score
$$R = \frac{1}{N} \sum_{i=1}^{N} \text{performance}(P_i)$$
Where:
- $R$ is the robustness score in range $[0, 100]$.
- $N$ is the number of perturbations tested.
- $P_i$ is the $i$-th perturbation applied (noise, dropout, unicode, etc.).
- $\text{performance}(P_i)$ is the average accuracy over trials.

### 3. Ablation Impact
$$\Delta_i = \text{performance}_{\text{full}} - \text{performance}_{\text{without\_engine\_}i}$$
Where:
- $\Delta_i$ is the accuracy degradation when component $i$ is disabled.
- $\text{performance}_{\text{full}}$ is the full pipeline accuracy.
- $\text{performance}_{\text{without\_engine\_}i}$ is the ablated pipeline accuracy.

## Usage

Create a `ValidationSuite`, add the tests, and run with `ValidationEngine`:

```python
from backend.validation import (
    ValidationEngine,
    ValidationSuite,
    LoadProfile,
    Perturbation,
    AblationStudy
)

# 1. Initialize Suite
suite = ValidationSuite("Core Pipeline Verification")

# 2. Add E2E and Unit modules
suite.add_unit_module("tests.test_models")
suite.add_e2e_test(
    test_name="Full RAG Flow",
    pipeline_fn=my_pipeline_callable,
    input_document=sample_doc,
    query="Who developed quantum mechanics?",
    expected_answer="Max Planck et al."
)

# 3. Add Stress profile
suite.add_stress_test(
    load_fn=lambda: my_pipeline_callable(sample_doc, "query"),
    profile=LoadProfile("Burst Load", num_requests=50, concurrency=5)
)

# 4. Add Robustness perturbation
suite.add_robustness_test(
    pipeline_fn=lambda text: my_pipeline_callable(text, "query"),
    original_input="Some input text",
    expected_output="Expected answer",
    perturbation=Perturbation.NOISE,
    perturbation_params={"level": 0.1}
)

# 5. Run Validation
engine = ValidationEngine(min_coverage_pct=95.0)
result = engine.run_suite(suite, output_dir="./reports")

print(f"Validation Status: {result.metrics.status}")
print(f"Pass Rate: {result.metrics.coverage_pct:.2f}%")
```
