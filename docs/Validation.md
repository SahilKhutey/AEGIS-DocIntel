# AMDI-OS Validation

This document describes the testing and validation framework ensuring the correctness, performance, and robustness of the AMDI-OS package.

---

## 1. Testing Hierarchy

AMDI-OS employs a 6-stage testing framework implemented under `backend/validation/` and verified in `tests/`:

```
┌─────────────────────────────────────────────────────────┐
│                    End-to-End (E2E)                     │
├─────────────────────────────────────────────────────────┤
│                Ablation Studies & Stress                │
├─────────────────────────────────────────────────────────┤
│                    Integration Tests                    │
├─────────────────────────────────────────────────────────┤
│                       Unit Tests                        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Validation Subsystems

### 2.1 Unit Testing
* **Objective**: Verifies the isolated mathematical behavior of individual engines, managers, and utility classes.
* **Coverage**: Core math modules, encryptors, role managers, token counters.
* **Command**:
```bash
python -m pytest tests/ -k "unit"
```

### 2.2 Integration Testing
* **Objective**: Verifies communications and data flow between multiple layers (e.g. Ingestion → Engines → Memory).
* **Coverage**: Ingestion pipeline, multi-representation parsing, index registration, token-budget context compilation.
* **Command**:
```bash
python -m pytest tests/ -k "integration"
```

### 2.3 End-to-End (E2E) Testing
* **Objective**: Validates the full request lifecycle from document upload through retrieval, connector query, and citation verification.
* **Command**:
```bash
python -m pytest tests/test_security_framework.py -v
```

---

## 3. Advanced Simulation Tests

### 3.1 Stress Testing
* **Objective**: Assesses pipeline throughput and system limits under heavy concurrent request volumes.
* **Methodology**: Simulate concurrent uploads and query streams up to 100 concurrent threads.
* **Metrics**: TPS, Latency percentiles (p50, p95, p99), error rates, CPU/RAM utilization.

### 3.2 Robustness Testing
* **Objective**: Validates that engines fail gracefully or remain stable when presented with corrupted, empty, massive, or maliciously perturbed inputs.
* **Fuzzing Parameters**:
  - Malformed PDF binary blocks.
  - Special characters and unicode boundary inputs.
  - Document sizes exceeding 1,000 pages.
  - Zero-length text chunks.

### 3.3 Ablation Studies
* **Objective**: Disables individual engines or retrieval methods to measure their specific impact on overall accuracy and retrieval success.
* **Metrics**: Reciprocal rank degradation, semantic coverage losses.