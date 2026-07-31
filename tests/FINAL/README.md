# Final Acceptance Tests

This directory is the **last word** on whether v0.3.0 is releasable.

* `test_acceptance_checklist.py` — parametric checks; one per
  box in `docs/FINAL_CHECKLIST.md`.
* `test_full_test_matrix.py` — runs the entire pytest tree.

## Run

```bash
pytest tests/FINAL -v
python scripts/verify_everything.py
```

## Pass criteria

* Every test in `test_acceptance_checklist.py` is green.
* `verify_everything.py` reports `OK · N/N invariants passed`
  (N = total checks listed under CHECKS in that script).
