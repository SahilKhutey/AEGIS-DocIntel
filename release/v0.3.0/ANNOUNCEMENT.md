# AEGIS-DocIntel v0.3.0 — "Deprecation Cleanup"

> **TL;DR:** v0.3.0 closes every deprecation window that v0.2.0 opened
> and adds the operational sweep-bots that keep them closed. Nothing
> user-visible should break; if your code already imports `amdi.*`, you
> can upgrade with `pip install --upgrade amdi-os` and move on.

## What's new

AEGIS-DocIntel is a *Pre-LLM Document Intelligence Operating System* —
the layer that turns a 200-page PDF into token-optimized, citation-anchored
context for any LLM. The v0.3.0 release focuses on the unsung 80% of
production work: deprecating old names, proving nothing has drifted,
and giving operators the metrics they need to keep the system healthy.

### Deprecation windows closed

* `from backend.src....` is **gone**. If you were relying on the
  `v0.2.0` BC shim, you have until `v0.4.0` to migrate. The sweep bot
  runs every night and files a PR the moment it spots a forbidden
  import.
* `from src.amdi....` now emits a `FutureWarning` that lights up your IDE
  and CI logs.
* All `amdi.legacy_bridge.*` names (the 12 engine renames, 7 ingestion
  renames, the retriever rename, and the PII engine rename) emit the
  same warning. The matrix that drives them is checked into the repo:
  `tools/deprecation_matrix.json`.

### Sweep bots ship

* `tools/sweep_drift.py` walks the source tree looking for forbidden
  imports and produces a JSON report. It's wired into nightly CI and to
  PR runs.
* `tools/sweep_openapi_sync.py` ensures the REST and gRPC contract stay
  in sync; if either side changes, the other must follow.
* `tools/sweep_audit_integrity.py` replays the SHA-256 hash-chained
  audit log and tells you the moment it's tampered with.
* `tools/sweep_dependency_audit.py` runs pip-audit and fails on
  HIGH/CRITICAL CVEs.

### Why this matters

Most RAG projects die because nobody checked if the context they handed
to the LLM was still safe, still relevant, and still inside the budget.
AEGIS-DocIntel now has a deterministic, CI-gated answer for all three.

## What you should do

* **If you consume the Python package** — upgrade with
  `pip install --upgrade amdi-os==0.3.0`. There are no breaking changes
  for anyone who already imported `amdi.*`.
* **If you maintain a fork** — re-run `python scripts/verify_migration.py`
  and accept the auto-PR the sweep bot opens (if any).
* **If you operate the system** — point Prometheus at the `/metrics`
  endpoint, import the dashboard JSON from `ops/grafana/dashboard.json`,
  and follow the runbook at `ops/prometheus/alerts/sre-runbook.md`.
* **If you just want to see it run** — `python scripts/demo_reel.py
  --record /tmp/check.json` performs the entire end-to-end scenario and
  saves a deterministic manifest you can diff against the golden trace.

## Looking forward

* **v0.4.0** removes the legacy bridge entirely.
* **v0.5.0** opens the federated-retrieval research track (multi-tenant
  vector routing).
* **v1.0.0** freezes the public API surface, promotes the four SDKs to
  semantic stability, and graduates the Helm chart to 1.0.0.

We publish the public roadmap at `docs/ROADMAP.md` and a one-page
shipping summary in every release post.

## Acknowledgements

AEGIS-DocIntel is the work of **Sahil Khutey** with the AI Research
Collaborator at *Gensouls Lab* (July 2026 Monograph Series, MIOS paper).
The v0.3.0 release was produced with assistance from the AEGIS
Sustaining Crew (see `docs/SUPPORT.md` for the maintainer roster).

— The AEGIS-DocIntel team
