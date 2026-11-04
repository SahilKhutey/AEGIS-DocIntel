# AEGIS-DocIntel — WP-08.05: Deployment Architecture

> **Work Package**: WP-08 — Integration (Work Item WP-08.05)  
> **Status**: **DEPLOYMENT ARCHITECTURE VERIFIED**  
> **Date**: 2026-11-04  
> **Target Environment**: Production Container Cluster & Staging Mirror  

---

## 1. System Deployment Overview

AEGIS-DocIntel is packaged as an immutable, hardened multi-tier containerized deployment managed via Docker Compose or Kubernetes, fronted by an Nginx TLS reverse proxy.

```mermaid
flowchart TD
    subgraph EdgeTier["1. Edge & Ingress Tier"]
        CLIENT[HTTPS Client Traffic] --> WAF[Cloudflare / Edge Firewall]
        WAF --> TLS[Nginx Reverse Proxy (:443)<br/>SSL Termination · Strict Headers · Rate Limiting]
    end

    subgraph AppTier["2. Application Tier (Hardened Containers)"]
        TLS -->|HTTP / Reverse Proxy| API[FastAPI Backend (:8000)<br/>Non-Root User · Read-Only RootFS · Drop Capabilities]
        TLS -->|HTTP / Web Traffic| FRONTEND[Next.js Web Workbench (:3000)<br/>Static & Prerendered Assets]
        API --> WORKERS[Background Worker Pool<br/>Lease Heartbeats · Idempotency Store · DLQ]
    end

    subgraph DataTier["3. Persistence & Messaging Tier"]
        API & WORKERS --> DB[(PostgreSQL Database<br/>Documents · Chunks · Audits · Tombstones)]
        API & WORKERS --> REDIS[(Redis In-Memory Store<br/>Job Queues · Leases · Semantic Cache)]
        API & WORKERS --> S3[MinIO S3 Object Storage<br/>Raw Documents · Layout Artifacts · Reports]
        API & WORKERS --> VEC[Vector Database Partition<br/>Tenant-Isolated Embeddings]
    end

    subgraph ObservabilityTier["4. Telemetry & Monitoring Tier"]
        API & WORKERS --> PROM[Prometheus (:9090)<br/>Latency, Error Rates, Queue Saturation]
        PROM --> GRAF[Grafana Dashboards (:3001)<br/>SLA Alerts & Pipeline Health]
    end
```

---

## 2. Hardened Container Specification

1. **User Privileges**: Container runs exclusively under non-root service account `aegis` (`UID=1000`).
2. **Filesystem Security**: Root filesystem is mounted strictly `read_only: true`. Ephemeral scratch space uses memory-backed `tmpfs` (`/tmp:rw,noexec,nosuid,size=256m`).
3. **Linux Capabilities**: Dropped all Linux capabilities (`cap_drop: ALL`) with `no-new-privileges: true`.
4. **Resource Constraints**: Capped at 2.0 CPUs and 2.0 GB memory with process thread limits (`pids_limit: 256`).
5. **Health Probing**: Liveness and readiness probed via `http://127.0.0.1:8000/health` with 30s interval, 5s timeout, and 3 retries.
