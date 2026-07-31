# Postmortem — 2026-07-15, ingestion slowdown (Sev-2)

## Summary

Between 14:03 and 14:47 UTC, the average `POST /v1/documents/upload`
p95 latency rose from 180 ms to 1.7 s. No 5xx errors. Mitigated at
14:51 by restarting the worker pool.

## Timeline (UTC)

* 14:03 — first dirty datapoint in Grafana
* 14:18 — on-call paged by SLO alert `AmdiHighLatency`
* 14:24 — worker pool size inspected: 3 (matches `replicaCount.worker`)
* 14:33 — memory inspection: worker pod RSS at 1.9 GiB (limit 2 GiB)
* 14:42 — rerouted Redis -> in-memory backend for ingest; no effect
* 14:47 — decided: rolling restart of worker pods
* 14:51 — p95 back to 190 ms

## Contributing factors

* A user-uploaded corpus of 60 PDFs (>= 200 pages each) ran inside the
  single-process OCR service and held the GIL for the duration of
  PyMuPDF `Page.get_text()`.
* No backpressure mechanism blocked additional jobs from being
  accepted, so the queue grew to 132 jobs.

## What went well

* SLO alert fired first; on-call was paged within a minute.
* No data loss; the audit log ran normally throughout.
* Rollback was a `kubectl rollout restart deploy/amdi-worker`.

## What we'll change (action items)

* [K-perf] Add PyMuPDF text-extraction to a thread pool — owner @TBD.
* [K-perf] Implement per-pod RSS alert at 80 % of limit.
* [K-obs] Add queue-depth dashboard panel.

## What we learned

The "production-grade" claim in v0.2.0 was true for *normal* workloads,
and we now have a clear precedent for what *abnormal* looks like.
