# Service Level Agreement — AEGIS-DocIntel (v0.3.0+)

This SLA applies to *managed* deployments of AEGIS-DocIntel (i.e., when
running with the Helm chart and observability stack from Deliverables G
and K enabled). Self-hosted, single-node installs inherit **only** the
data integrity and security promises; availability is at the operator's
discretion.

## 1. Definitions

| Term | Meaning |
| ---- | ------- |
| **Production** | A deployment handling > 0 user requests in 24 h |
| **Incident** | An event causing measurable degradation or outage |
| **Severity 1** | Total outage for > 1 user OR loss of data integrity |
| **Severity 2** | Partial degradation (e.g. one engine failing; rest OK) |
| **Severity 3** | Cosmetic / non-blocking issues |

## 2. Uptime targets

| Tier | Monthly availability | Allowed downtime |
| ---- | -------------------- | ---------------- |
| Production managed (multi-AZ) | >= 99.9 % | <= 43 min / month |
| Production single-node | >= 99.0 % | <= 7 h  / month |

We **measure** uptime with the synthetic probes defined in
`ops/probes/synthetic.yml`. The probes run from at least two external
regions every 30 s.

## 3. Performance targets

| KPI | Target | Where measured |
| --- | ------ | -------------- |
| `POST /v1/documents/upload` p95 | <= 250 ms | `histogram_quantile(0.95, ...)` |
| `POST /v1/query/` p95 (cached) | <= 700 ms | same |
| `POST /v1/query/` p95 (cold) | <= 2.5 s | same |
| `GET  /v1/jobs/{id}/events` TTFB | <= 100 ms | "time-to-first-byte" log field |
| Token-budget adherence | 100 % | `tests/export/test_budget_hard_cap.py` |

Targets are reviewed at every minor release. If your workload requires
different numbers, open an issue labelled `K-policy` with the prefix
`SLA:`.

## 4. Incident response

| Severity | Acknowledge | Mitigate | Root-cause notes |
| -------- | ----------- | -------- | ---------------- |
| Sev-1 | <= 1 hour | <= 4 hours | <= 7 days (post-mortem) |
| Sev-2 | <= 4 hours | <= 24 hours | <= 14 days |
| Sev-3 | <= 2 days | Next minor | Next minor |

See `docs/POSTMORTEMS/` for the format. (We publish a postmortem for
every Sev-1 within seven calendar days.)

## 5. Backup & recovery

* **RPO** (Recovery Point Objective): **5 minutes**. The job ledger
  persists every progress event to disk with fsync; the worst loss is
  whatever happened in the last 5 minutes.
* **RTO** (Recovery Time Objective): **30 minutes** for a single-AZ
  restore, **5 minutes** for a multi-AZ hot-failover.

## 6. Data integrity

The audit chain (`tools/sweep_audit_integrity.py`) is run nightly. A
broken chain triggers a Sev-2 within one business day.

## 7. What we explicitly do not promise

* Latency to upstream LLM providers (OpenAI, Anthropic, etc.).
* Throughput of arbitrary third-party OCR engines.
* Anything outside the AEGIS-DocIntel codebase.
