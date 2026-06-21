"""
AMDI-OS Security Framework
============================

Comprehensive security layer covering:

    - Encryption         : AES-256, RSA, hashing
    - Access Control     : RBAC + ABAC
    - Authentication     : JWT / API key / OAuth
    - Audit Logs         : tamper-evident event log
    - Secret Management  : Vault-like secret storage

Mathematical Foundation:
    AES-256:
        E_k(m) = AES(m, k)   where k ∈ {0,1}^256

    RSA:
        c = m^e mod n        (encrypt)
        m = c^d mod n        (decrypt)

    JWT signature:
        σ = HMAC-SHA256(secret, header.payload)

    RBAC permission check:
        P(user, resource, action) = user.role ⊆ action ⊆ resource.permissions

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .security_engine import SecurityEngine, SecurityReport
from .encryption import (
    EncryptionManager,
    AESEncryptor,
    RSAEncryptor,
    HashManager,
    EncryptedData,
)
from .access_control import (
    AccessController,
    Role,
    Permission,
    Resource,
    Policy,
    AccessDecision,
)
from .authentication import (
    AuthenticationManager,
    AuthToken,
    User,
    APIKey,
)
from .audit_log import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
)
from .secret_manager import (
    SecretManager,
    Secret,
    SecretMetadata,
)
from .security_middleware import SecurityMiddleware
from .rate_limiter import RateLimiter, RateLimitRule
from .threat_detector import (
    ThreatDetector,
    ThreatLevel,
    ThreatIndicator,
)
from .security_report import (
    SecurityReportData,
    SecurityMetrics,
)
from .exceptions import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    EncryptionError,
    SecretAccessError,
)

__all__ = [
    "SecurityEngine",
    "SecurityReport",
    "EncryptionManager",
    "AESEncryptor",
    "RSAEncryptor",
    "HashManager",
    "EncryptedData",
    "AccessController",
    "Role",
    "Permission",
    "Resource",
    "Policy",
    "AccessDecision",
    "AuthenticationManager",
    "AuthToken",
    "User",
    "APIKey",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "SecretManager",
    "Secret",
    "SecretMetadata",
    "SecurityMiddleware",
    "RateLimiter",
    "RateLimitRule",
    "ThreatDetector",
    "ThreatLevel",
    "ThreatIndicator",
    "SecurityReportData",
    "SecurityMetrics",
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    "EncryptionError",
    "SecretAccessError",
]

__version__ = "1.0.0"
