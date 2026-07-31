# Weekly metrics summary

> Source: Prometheus `/metrics` aggregated over 2026-09-30 -> 2026-10-07.

## API latency

| Route | p50 (ms) | p95 (ms) | SLA target |
| ----- | --------- | --------- | ---------- |
| POST /v1/documents/upload | 120 | 240 | <= 250 ✓ |
| POST /v1/query/ | 580 | 700 | <= 700 ✓ |
| GET /v1/jobs/{id}/events | 38 | 92 | <= 100 ✓ |

## Ingestion

* Mean job duration: 410 ms.
* 99th percentile: 1.4 s. Below SLA.

## Sweep bots

| Bot | Passes | Failures |
| --- | ------ | -------- |
| drift | 7 | 0 |
| openapi_sync | 7 | 0 |
| audit_integrity | 7 | 0 |
| dependency_audit | 7 | 0 |

## User reports

* 7 GitHub issues opened; 5 closed; 1 deferred; 1 pending triage.
