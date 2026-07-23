# Archived Trees

These three directories were confirmed, by direct inspection (Repository
Audit, Finding 1; corrected and re-verified in a follow-up session — see
below), to be orphaned: zero files anywhere in `src/` or `backend/` import
from any of them, and `tests/conftest.py` already contained a deliberate
`ProtectedPathList` guard explicitly blocking `amdi-os` from `sys.path`,
with a comment confirming `src/` as "the unified 'src' folder" — primary
evidence, predating this archival, that this was already the intended
state.

## Correction to the original audit's Finding 1

The original Repository Audit reported "204 differing files, 0 identical"
between `src/` and `amdi-os/src/`, framed as two independently-diverged
implementations requiring a file-by-file, two-reviewer reconciliation
before any consolidation. That comparison did not exclude `__pycache__/`
and `*.pyc` files. Re-run excluding compiled bytecode noise, the true
source-level difference was **17 items**, not 204 — and of those 17:

- 5 (`main.py`, `services/`, `observability/`, `memory_engine/`,
  `llm_service/`) exist only in `src/` — meaning `amdi-os/src/` cannot
  serve as an application entry point at all (no `main.py`).
- 2 (`annotations.py`, `api_server.py`) exist only in `amdi-os/src/api/`,
  and are directly superseded by `src/api/routers/annotations.py` and
  `src/main.py` respectively (confirmed by reading both).
- The remainder (`config.py`, `cli.py`, `__init__.py`, and others) are
  earlier/smaller versions of their `src/` counterparts (e.g. `config.py`:
  67 lines in `amdi-os/src/` vs. 235 in `src/`), consistent with
  `amdi-os/` being an earlier development snapshot, not a parallel
  evolution.
- Within the entire `engines/` subtree specifically — the mathematical
  core this project's documentation makes its strongest claims about —
  `src/` and `amdi-os/src/` were **byte-identical except for one file**
  (`semantic_engine.py`, already fixed in `src/` in a prior pass; see
  `docs/audit/` or the relevant patch notes).

This is a materially different, much lower-risk finding than the original
"0 identical files" framing suggested, and this archival — rather than the
originally-planned full 204-file manual reconciliation — is the
appropriately-scoped action given that corrected evidence.

## Why archived, not deleted

Git history preserves everything regardless, but these directories are
moved rather than `git rm`'d outright so that (a) the move is trivially
reversible by inspecting `_archive/` directly without needing to dig
through git log, and (b) this specific decision — the one part of this
consolidation with any real judgment call in it — gets a visible,
easy-to-review diff rather than a silent deletion, consistent with this
project's own stated two-reviewer discipline for exactly this kind of
change.

## What was NOT lost

`amdi-os/mios/`'s twelve-engine module structure was the one part of
this tree with test coverage (`tests/test_mios.py`) not already
duplicated against `src/engines/`. That coverage gap was identified,
verified, and closed in a prior pass: four engines (Topology, Spectral,
InfoPhysics, Tensor) already had passing tests against `src/engines/`;
the other five (Bayesian, Markov, Decision, Optimization, Economics) plus
Meta-Learning, RL, and an orchestrator integration test were ported to
`tests/test_optimization_suite_engines.py`, which now tests `src/engines/`
directly. `tests/test_mios.py` was removed as part of that same change.
