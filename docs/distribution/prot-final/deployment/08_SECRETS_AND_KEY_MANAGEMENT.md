# Secrets & Key Management Lifecycle (DEP-07)

## Secret Inventory & Purpose Separation
- `jwt_signing_key`: Identity authentication.
- `license_signing_key`: License Ed25519 signing.
- `internal_service_secret`: Gateway-to-Engine HMAC-SHA256.
- `database_password`: PostgreSQL SCRAM-SHA-256 credentials.
- `openai_api_key` / `anthropic_api_key`: Outbound LLM inference.
- `tls_private_key`: Edge reverse proxy TLS termination.

Keys are segregated by purpose; reusing a key across multiple purposes is rejected by policy (`DEP-TEST-007`).
