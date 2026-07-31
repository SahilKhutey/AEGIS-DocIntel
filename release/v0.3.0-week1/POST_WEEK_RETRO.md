# First-week retro (v0.3.0 -> v0.3.1)

**Date:** 2026-10-07
**Facilitator:** on-call (Alice)
**Attendees:** Alice, Bob, Carol

## What went well
- Release-yml hit green within 8 minutes.
- Sweep bots caught drift on day 2 before any user saw it.
- Three community PRs landed cleanly.

## What surprised us
- Python 3.13 hit harder than expected. We held 3.12 as primary; we'll
  make 3.13 official at 0.4.0.
- The PII redaction bug had been latent since v0.2.0 and only surfaced
  when a customer uploaded Japanese text.

## What we'll change (action items)
- [K-perf] Add PII test corpus with multilingual fixtures (owner @Bob).
- [K-bot] Tighten `sweep_drift.py` regex to ignore string literals (#1045).
- [K-policy] Expand SLA scope to include image-based ingestion.

## Lessons learned
- "Production-ready" claims require a representative workload — multilingual
  was missing from our golden trace. Added to roadmap.
- A single-file SLA isn't enough; we should publish a public "status" page
  that mirrors the runbook.
