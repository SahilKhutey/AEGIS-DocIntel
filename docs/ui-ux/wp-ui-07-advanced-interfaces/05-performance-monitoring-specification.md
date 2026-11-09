# 05 — Performance Monitoring Specification

## 1. Functional Scope
The Performance Monitoring Workspace (`/monitoring`) delivers real-time infrastructure observability, latency percentiles, worker utilization, and operational alerts.

## 2. Telemetry Ingestion
- `GET /health/ready`: Assesses critical dependencies (FastAPI gateway, PostgreSQL, Vector database, S3 object storage).
- `GET /health/live`: Probes process responsiveness and uptime.
- `GET /v1/admin/stats`: Supplies query latency and cache efficiency.

## 3. SLA Percentile Tracking
Query latency is tracked across key percentiles:
- **P50 (Median)**: Baseline user experience (Target: < 100ms)
- **P90**: High-percentile performance
- **P95**: Contractual SLA boundary (Target: < 300ms)
- **P99**: Outlier tail latency under peak system load

## 4. Freshness & Alert Handling
- **Freshness Badge (`FreshnessBadge.tsx`)**: Displays relative seconds elapsed since the last telemetry poll with manual refresh capability.
- **Alert Dispatch (`AlertsList.tsx`)**: Categorizes alerts into `critical`, `warning`, and `info` with one-click acknowledgment.
