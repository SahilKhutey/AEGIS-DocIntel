# AEGIS-DocIntel — Audit Configuration Specification

## Profiles

1. **`default.yaml`**: Standard complete audit profile for routine development sweeps.
2. **`development.yaml`**: Fast fail-fast profile targeting unit tests only with reduced timeouts.
3. **`ci.yaml`**: Automated CI profile with strict validation and artifact retention.
4. **`strict.yaml`**: Release gate profile. Disallows dirty git working trees, requires evidence collection, and enforces full suite verification.

## Semantic Rules (CFG-001 through CFG-010)

| Rule ID | Name | Enforcement Invariant |
| :--- | :--- | :--- |
| **CFG-001** | Version Supported | Version must match `1.0` or `1.0.0`. |
| **CFG-002** | Suite IDs Unique | Duplicate suite declarations are rejected. |
| **CFG-003** | Suite Registered | Declared suites must exist in `AuditRegistry`. |
| **CFG-004** | Timeout Positive | Global and per-suite timeouts must be positive numbers. |
| **CFG-005** | Retries Valid | Retries must be an integer between 0 and 5. |
| **CFG-006** | Parallelism Valid | `max_parallel_suites` must be an integer $\ge 1$. |
| **CFG-007** | Required Enabled | Contradiction check: `required: true` with `enabled: false` is rejected. |
| **CFG-008** | Evidence Enabled | Evidence collection cannot be disabled in strict mode. |
| **CFG-009** | Safe Output Dir | Output directory must not contain path traversal (`..`). |
| **CFG-010** | Traceability Strict | Commit and environment traceability cannot be disabled in strict mode. |
