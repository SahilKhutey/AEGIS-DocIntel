# Maintainer playbook

## Daily (≤ 10 min)

* Review sweep-bot PRs; merge or block same-day.

## Weekly (≤ 30 min)

* Triage new issues; apply labels.
* Review security advisories.
* Run `python scripts/weekly_digest.py` and post to #release.

## Per release candidate

* Run `scripts/release_preflight.py`.
* Confirm `tools/sweep_*.py` all green.
* Tag and push; `release.yml` runs.
* Smoke-test `pip install amdi-os==X.Y.Z`.

## Decision matrix

| Question | Answer |
| -------- | ------ |
| Should we add a new engine? | Yes, if it improves precision/recall ≥ 5 % |
| Should we add a new SDK language? | After two paid contracts justify it |
| Should we remove a deprecated symbol early? | No — wait for the next-minor window |
| Should we bump matplotlib in `benchmarks` extras? | No — stay on LTS |
