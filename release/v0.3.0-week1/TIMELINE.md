# v0.3.0 — Week-One Timeline (2026-09-30 -> 2026-10-07)

## Day 1 (Wed, 2026-09-30) — TAG DAY
* 14:00 UTC — `bash ops/release/tag-v0.3.0.sh` -> tag pushed
* 14:08 UTC — `release.yml` GitHub Action green
* 14:12 UTC — `ghcr.io/sahilkhutey/amdi:v0.3.0` manifest verified
* 14:24 UTC — announcement published to GitHub Releases
* 14:31 UTC — `site/press/2026-09-30-v0.3.0.md` PR merged (auto by bot)
* 14:40 UTC — README badge pin PR merged
* 15:00 UTC — initial user reports begin (see TRIAGE_LOG.md)
* 17:00 UTC — sweep-bot nightly begins producing JSON

## Day 2 (Thu, 2026-10-01)
* 09:11 UTC — drift sweeper flagged 3 internal references that need rewriting
* 10:04 UTC — replacement PR merged via `bot/sweep-drift-*` branch
* 11:30 UTC — first CI flake on `tests/export/test_budget_hard_cap.py`
  (non-deterministic at budget=128 with random input) — repro'd locally,
  not a release blocker
* 14:00 UTC — first weekly digest draft

## Day 3 (Fri, 2026-10-02)
* 06:00 UTC — first weekly sweep aggregation ran (4 sweeps, all green)
* 10:00 UTC — user-facing Sev-3: PII redaction pattern missed non-Latin
  phone numbers — filed as #1042
* 13:00 UTC — community PR #1044 (Python SDK example improvement)
* 16:30 UTC — webhook ping: dependabot opened `deps: bump httpx` — auto-merge blocked on K-bot

## Day 4 — Day 6 (Sat–Mon)
* Quiet weekend. Sweep bots green; synthetic probes all green.

## Day 7 (Tue, 2026-10-07)
* Mon 09:00 UTC — on-call rotation handoff (see ops/oncall/rotation.md)
* Mon 14:00 UTC — formal triage session; v0.3.1 CHANGELOG seeds committed
* Tue 10:00 UTC — patch release candidate v0.3.1-rc.1 cut
