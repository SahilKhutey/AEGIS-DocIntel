# Deployment Configuration & Compose Specification (DEP-11)

## Production Manifest Validation
- `infrastructure/compose/production/docker-compose.yml` satisfies all zero-trust requirements (`DEP-TEST-008`).
- Secrets injected via Docker Secrets (`/run/secrets/*`), with zero plaintext secrets committed to source control.
- Internal networks configured with `internal: true`.
