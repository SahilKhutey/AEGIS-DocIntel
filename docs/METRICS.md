# Metrics — the ones that matter

AEGIS-DocIntel exposes Prometheus metrics at `/metrics`. Not every
metric deserves an alert. Below is the curated list **on** by default.

## API health

| Metric | Use |
| ------ | --- |
| `amdi_http_requests_total` | Per-route volume & 4xx/5xx rate |
| `amdi_http_request_duration_seconds` | Latency SLO tracking |
| `amdi_jobs_running` | Worker saturation |
| `amdi_jobs_failed_total{reason=...}` | Failure attribution |
| `amdi_retrieval_recall_at_k_bucket` | Quality guard (set by `benchmarks/run_all`) |

## Security

| Metric | Use |
| ------ | --- |
| `amdi_grpc_requests_total{code=...}` | Auth/perm denials |
| Audit-chain integrity | Reported from `tools/sweep_audit_integrity.py` (cron) |

## Bootstrapping Prometheus + Grafana

The Helm chart in `ops/helm/amdi/` ships:

* `templates/servicemonitor.yaml` — auto-discovery for Prometheus.
* Runbook: `docs/POSTMORTEMS/2026-07-15-ingestion-slow.md` shows the
  exact Grafana panel that caught the incident.
