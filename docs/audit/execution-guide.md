# AEGIS-DocIntel — Audit Infrastructure Execution Guide

## CLI Usage

The audit infrastructure can be executed via `python -m aegis.audit` or `python scripts/audit.py`.

### 1. List Available Audit Suites
```bash
python -m aegis.audit list
```

### 2. Validate Configuration
```bash
python -m aegis.audit validate --config configs/audit/default.yaml
python -m aegis.audit validate --config configs/audit/strict.yaml
```

### 3. Preview Execution Plan (Dry-Run)
```bash
python -m aegis.audit plan --config configs/audit/default.yaml
python -m aegis.audit run --config configs/audit/default.yaml --dry-run
```

### 4. Execute Full Audit
```bash
python -m aegis.audit run --all --config configs/audit/default.yaml
```

### 5. Execute Specific Suite
```bash
python -m aegis.audit run --suite unit
python -m aegis.audit run --suite security --suite integration
```

### 6. Inspect Past Run
```bash
python -m aegis.audit inspect AG-20261103-034841-RQ1E
```

### 7. Verify Evidence Integrity
```bash
python -m aegis.audit verify AG-20261103-034841-RQ1E
```

### 8. Historical Diff & Regression Comparison
```bash
python -m aegis.audit compare AG-20261103-034841-RQ1E AG-20261103-034858-7T5B
```
