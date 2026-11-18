# 06 - Download Portal Specification
- **Security Boundary**: Public release endpoint requiring authenticated token.
- **Download Token**: 256-bit cryptographically secure token with 15-minute TTL.
- **Integrity**: Every artifact download accompanied by published SHA-256 hash and Ed25519 signature.
- **Audit**: All download attempts (success/failure) recorded with client IP and evaluator ID.
