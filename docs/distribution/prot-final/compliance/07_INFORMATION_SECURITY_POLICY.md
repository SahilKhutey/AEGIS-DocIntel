# Information Security Policy (POL-005)

## Mandatory Security Principles
- **Least Privilege:** Database users (`aegis_app`) restricted to DML operations; DDL strictly denied.
- **Defense in Depth:** Edge TLS termination, HMAC service-to-service authentication, and private network segmentation.
- **Zero Hardcoded Secrets:** Docker Secrets and KMS injection; immediate release failure if credentials detected.
- **Audit Immutability:** Security events cryptographically chained via SHA-256 hash registers.
