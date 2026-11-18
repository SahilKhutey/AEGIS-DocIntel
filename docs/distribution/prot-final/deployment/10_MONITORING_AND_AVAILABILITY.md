# Monitoring, Metrics & Availability Specification (DEP-09)

## Health Probes
- `/health/live`: Lightweight liveness probe returning process status.
- `/health/ready`: Readiness probe verifying internal registry and quota subsystems.
- Zero sensitive data exposure: Internal IP addresses, database hostnames, and stack traces are redacted (`DEP-TEST-015`).

## Operational Targets
- Gateway Availability Target: 99.5%
- Gateway p95 Latency (excluding engine processing): < 500 ms
- Revocation Propagation: < 60 seconds
- Recovery Point Objective (RPO): < 24 hours
- Recovery Time Objective (RTO): < 4 hours
