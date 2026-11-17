# PROT-04.08 — Dossier 02: Security Event Taxonomy & Schema

## 1. Taxonomic Classification
The AEGIS-DocIntel platform classifies all security events into 6 functional operational categories comprising **36 canonical event types**. Every event type has a predetermined baseline severity level: `INFO`, `WARNING`, `HIGH`, or `CRITICAL`.

### Category 1: Authentication & Identity
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `AUTH_SUCCESS` | `INFO` | Successful evaluator authentication via valid token or API key. |
| `AUTH_FAILURE` | `WARNING` | Failed authentication due to invalid credentials or expired token. |
| `AUTH_TOKEN_REJECTED` | `WARNING` | Malformed, corrupted, or unsupported token presented. |
| `DEV_TOKEN_ATTEMPT` | `CRITICAL` | Evaluator attempted to present a prohibited development token (`dev-*`). |

### Category 2: Evaluation License Lifecycle
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `ACTIVATION_SUCCESS` | `INFO` | Successful activation and node binding with valid activation code. |
| `ACTIVATION_FAILURE` | `WARNING` | Unsuccessful activation attempt (invalid code, expired code, rate limit). |
| `LICENSE_ISSUED` | `INFO` | Server generated and signed a new Ed25519 evaluation license. |
| `LICENSE_VERIFIED` | `INFO` | Evaluator license verified successfully against server public key. |
| `LICENSE_EXPIRED` | `WARNING` | Request blocked due to elapsed license expiration timestamp. |
| `LICENSE_REVOKED` | `HIGH` | Request blocked due to license revocation entry in authoritative registry. |
| `LICENSE_TAMPER_DETECTED` | `CRITICAL` | License payload cryptographic signature verification failed. |
| `DEVICE_REGISTERED` | `INFO` | New hardware fingerprint bound to evaluation license. |
| `DEVICE_LIMIT_EXCEEDED` | `WARNING` | Activation blocked because license has reached maximum device allocation. |

### Category 3: Entitlement & Quota Enforcement
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `ENTITLEMENT_ALLOWED` | `INFO` | Requested capability permitted by evaluation license tier. |
| `ENTITLEMENT_DENIED` | `WARNING` | Evaluator attempted operation not permitted by license tier. |
| `QUOTA_CONSUMED` | `INFO` | Units consumed and decremented from evaluation quota ledger. |
| `QUOTA_EXCEEDED` | `WARNING` | Operation rejected due to exhausted quota balance. |
| `QUOTA_RECONCILIATION_MISMATCH` | `HIGH` | Ledger drift detected between fast memory cache and persistent store. |

### Category 4: Session Lifecycle & Tokens
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `SESSION_CREATED` | `INFO` | New evaluation session initiated with short-lived access token. |
| `SESSION_REFRESHED` | `INFO` | Refresh token presented, rotated, and new token pair issued. |
| `SESSION_REVOKED` | `INFO` | Single session terminated explicitly via user or admin logout. |
| `ALL_SESSIONS_REVOKED` | `HIGH` | Cascading invalidation of all sessions for evaluator or tenant. |
| `REFRESH_REUSE_DETECTED` | `CRITICAL` | Consumed refresh token presented; immediate token family revocation. |
| `WS_TICKET_ISSUED` | `INFO` | Ephemeral single-use WebSocket authentication ticket generated. |
| `WS_TICKET_CONSUMED` | `INFO` | WebSocket ticket validated and invalidated upon socket handshake. |
| `WS_AUTH_FAILURE` | `WARNING` | WebSocket connection attempt rejected due to invalid or expired ticket. |

### Category 5: Integrity, Auditing & Monitoring
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `CHAIN_HASH_CALCULATED` | `INFO` | New cryptographic block chained onto sequential audit trail. |
| `CHAIN_TAMPER_DETECTED` | `CRITICAL` | Audit chain verification discovered broken hash continuity or tampering. |
| `CHECKPOINT_CREATED` | `INFO` | External signed audit checkpoint generated. |
| `ALERT_TRIGGERED` | `HIGH` | Threat detection engine matched rule condition (MON-001..012). |
| `ALERT_DELIVERY_FAILURE` | `HIGH` | Security sink webhook or syslog destination unreachable. |
| `DEGRADED_MODE_ENTERED` | `CRITICAL` | Monitoring subsystem degraded; platform operating fail-closed. |

### Category 6: Administrative & Incident Operations
| Event Type | Default Severity | Description |
| :--- | :--- | :--- |
| `KEY_ROTATION` | `INFO` | Ed25519 signing key rotated; predecessor moved to `VERIFY_ONLY`. |
| `KEY_COMPROMISE_REPORTED` | `CRITICAL` | Emergency administrative invalidation of compromised signing key. |
| `SECRET_ROTATION` | `INFO` | API key or service token rotated and invalidated. |
| `INCIDENT_DECLARED` | `HIGH` | Security operator opened formal incident investigation. |
| `INCIDENT_CONTAINED` | `INFO` | Containment actions executed (session revoked, IP blocked). |
| `INCIDENT_CLOSED` | `INFO` | Incident resolved with attached forensic evidence artifacts. |

---

## 2. Pydantic v2 Schema Specification
All events emitted by backend services and gateway ingress adhere to `SecurityEvent` in `src/security/event_schema.py`:

```python
class SecurityEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    severity: Severity
    result: str  # "allowed", "denied", "error", "success", "critical"
    tenant_id: Optional[str] = None
    evaluator_id: Optional[str] = None
    device_id: Optional[str] = None
    license_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    source_ip: Optional[str] = None
    reason_code: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    schema_version: int = Field(default=1, frozen=True)
```

### Invariants:
1. **Extra Field Rejection**: `extra="forbid"` ensures that unexpected client fields cannot be smuggled into audit records.
2. **Immutability**: `frozen=True` ensures that event records cannot be altered in memory once constructed.
3. **Canonical Categorization**: Unknown event types are dynamically assigned `Severity.HIGH` to prevent threat blindspots.
