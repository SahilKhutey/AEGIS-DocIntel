# Security & Compliance — Deployment Assumptions

This document states explicitly what this codebase assumes its deployment
environment provides, versus what it enforces itself. Anyone deploying this
system is responsible for the "environment provides" column.

| Control | This codebase | The deployment environment must provide |
|---|---|---|
| TLS / encryption in transit | No code-level enforcement | A TLS-terminating reverse proxy/load balancer in front of the app |
| `AEGIS_ENVIRONMENT` variable | Defaults fail-safe to "production" | Must NOT be set to "development" in any real deployment (see Phase 10) |
| Document persistence | Currently in-memory only (see STATUS.md) | N/A until Phase 11.2's persistent-store work lands — do not deploy this for real user data yet |
| Encryption at rest | Not implemented | N/A — no persistent store exists yet to encrypt |
| Network isolation | `0.0.0.0` bind is the default (Phase 10) | A firewall/security-group restricting inbound access appropriately |
