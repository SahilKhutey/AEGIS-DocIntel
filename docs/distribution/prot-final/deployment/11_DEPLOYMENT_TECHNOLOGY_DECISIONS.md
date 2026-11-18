# Deployment Technology Decisions (DEP-10)

## Technology Stack
- **Containerization:** Docker & Docker Compose with rootless container execution (`user: "10001:10001"`, `no-new-privileges:true`).
- **Edge Reverse Proxy:** Caddy 2.8 Alpine with automated TLS termination and security header injection.
- **Gateway Runtime:** FastAPI / Uvicorn running Python 3.12-slim.
- **Transactional Database:** PostgreSQL 17 Alpine with SCRAM-SHA-256 authentication and parameterized schemas.
- **Monitoring:** Prometheus metric scrapers isolated to internal networks.
