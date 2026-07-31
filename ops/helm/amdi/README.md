# AEGIS-DocIntel Helm Chart

## Install

```bash
helm upgrade --install amdi ./ops/helm/amdi \
    --namespace amdi --create-namespace \
    --set jwtSecret=$(openssl rand -base64 48) \
    --set redis.auth.existingSecret=amdi-redis \
    --set redis.auth.key=password
```

## Components

- **api**        — FastAPI + gRPC + metrics. HPA on CPU.
- **worker**     — arq ingest workers. HPA on `amdi_jobs_running`.
- **redis**      — bundled redis when `redis.enabled=true`.
- **prometheus** — rule-based SLO alerts.
- **grafana**    — per-routed dashboard.
- **ingress**    — TLS termination; SSE-friendly timeout.

## Operational notes

- **JWT secret** is required (`jwtSecret=...`). Rotate quarterly.
- **PVC `amdi-data`** holds the audit log; back it up off-cluster.
- **Audit chain** — verify integrity nightly:

      docker exec amdi-api python -m amdi.security.audit_verify /var/lib/amdi/audit
