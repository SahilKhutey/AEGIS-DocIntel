# AMDI-OS Security Framework

Comprehensive security layer covering:
- **Encryption**: AES-256-GCM symmetric encryption, RSA-2048 asymmetric key exchange/signatures/verification, and cryptographic hashing.
- **Access Control**: Role-Based Access Control (RBAC) + Attribute-Based Access Control (ABAC) with priority-sorted policy evaluation.
- **Authentication**: JWT-based stateless tokens and cryptographically secure API keys, complete with password hashing.
- **Audit Logs**: A tamper-evident event log utilizing hash chains to detect modifications.
- **Secret Management**: A Vault-like secure storage mechanism featuring versioned history, access policies, encryption at rest, and audit logs.
- **Rate Limiting**: Sliding window rate limiting to protect endpoints.
- **Threat Detection**: Input security scanning to detect SQL injection, Cross-Site Scripting (XSS), and Path Traversal.
- **Security Middleware**: FastAPI-compatible ASGI middleware.

## Mathematical Foundation

### AES-256 Symmetric Encryption
Authenticated Encryption with Associated Data (AEAD) using AES-256-GCM:
$$E_k(m) = \text{AES-GCM}(m, k) \quad \text{where } k \in \{0,1\}^{256}$$

### RSA-2048 Asymmetric Encryption
KeyPair generation and asymmetric encryption/decryption:
$$c = m^e \pmod n \quad (\text{encryption})$$
$$m = c^d \pmod n \quad (\text{decryption})$$

### JWT Signatures
Signed web tokens using HMAC-SHA256:
$$\sigma = \text{HMAC-SHA256}(\text{secret}, \text{header} \mathbin{\Vert} \text{payload})$$

### RBAC Permission Check
Access validation through role hierarchy:
$$P(\text{user}, \text{resource}, \text{action}) = \text{user.role} \subseteq \text{action} \subseteq \text{resource.permissions}$$

## Directory Layout
- `__init__.py`: Package entry point.
- `security_engine.py`: Central coordinator orchestrating all managers.
- `encryption.py`: AES, RSA, and hashing managers.
- `access_control.py`: Roles and policy engine.
- `authentication.py`: User registration, passwords, JWT, and API keys.
- `audit_log.py`: Tamper-evident blockchain-like hash logger.
- `secret_manager.py`: Versioned, encrypted secret key store.
- `rate_limiter.py`: Sliding window client rate limiter.
- `threat_detector.py`: Scans inputs for SQLi, XSS, and path traversal patterns.
- `security_report.py`: Compile security summaries and metrics.
- `security_middleware.py`: FastAPI interceptor middleware.
- `hash_compat.py`: Password hashing using `bcrypt`.
- `exceptions.py`: Custom security exceptions.
