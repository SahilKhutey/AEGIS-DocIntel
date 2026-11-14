# WP-04.05 Dossier 05: Policy Evaluation Engine

**Work Package:** PROT-04.05  
**Title:** Policy Evaluation Engine & Authorization Decision Algorithm  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Subsystem Architecture

The evaluation engine is organized into decoupled services, repositories, and cache layers:

```mermaid
flowchart LR
    Caller["API Route / Gateway Handler"] --> Service["EntitlementService<br/>(authorize)"]
    Service --> Cache["EntitlementCache<br/>(Short-lived, revision-aware)"]
    Service --> Resolver["EntitlementResolver"]
    Resolver --> PolicyRepo["EntitlementPolicyRepository"]
    Resolver --> EntRepo["EntitlementRepository<br/>(Assignments & Overrides)"]
    Service --> EventRepo["EntitlementEventRepository<br/>(Append-Only Log)"]
    Service --> Decision["AuthorizationDecision<br/>(allowed, reason_code)"]
```

---

## 2. Evaluation Resolution Sequence

When `EntitlementService.authorize()` is invoked for an incoming request, it executes the following sequential verification gates:

```mermaid
sequenceDiagram
    autonumber
    participant Caller as FastAPI Dependency
    participant Service as EntitlementService
    participant Cache as EntitlementCache
    participant Resolver as EntitlementResolver
    participant Repo as EntitlementRepository
    participant Audit as EntitlementEventRepository

    Caller->>Service: authorize(principal, permission, feature, resource)
    Service->>Service: 1. RBAC Guard: Verify principal has no admin roles
    alt Admin role detected on evaluator
        Service->>Audit: Log ADMIN_ROLE_PROHIBITED
        Service-->>Caller: Decision(allowed=False, reason="ADMIN_ROLE_PROHIBITED")
    end

    Service->>Service: 2. License Guard: Verify status is ACTIVE (not EXPIRED/SUSPENDED/REVOKED)
    alt License not active
        Service->>Audit: Log LICENSE_EXPIRED / LICENSE_REVOKED
        Service-->>Caller: Decision(allowed=False, reason=status)
    end

    Service->>Service: 3. Device Guard: Verify device is active and bound
    alt Device inactive
        Service->>Audit: Log DEVICE_INACTIVE
        Service-->>Caller: Decision(allowed=False, reason="DEVICE_INACTIVE")
    end

    Service->>Cache: 4. Check Cache(license_id, feature, permission, revision)
    alt Cache Hit
        Cache-->>Service: (allowed, reason_code)
    else Cache Miss
        Service->>Resolver: evaluate_permission(license_id, feature, permission)
        Resolver->>Repo: Get assignment & active overrides
        Resolver->>Resolver: Evaluate feature & action permission
        Resolver-->>Service: (allowed, reason_code)
        Service->>Cache: Set cache entry
    end

    alt Not Entitled
        Service->>Audit: Log FEATURE_NOT_GRANTED
        Service-->>Caller: Decision(allowed=False, reason=reason_code)
    end

    Service->>Service: 5. Resource Guard: Verify tenant_id matches resource.tenant_id
    alt Cross-tenant mismatch
        Service->>Audit: Log CROSS_TENANT_ACCESS_DENIED
        Service-->>Caller: Decision(allowed=False, reason="CROSS_TENANT_ACCESS_DENIED")
    end

    Service->>Audit: Log ALLOWED
    Service-->>Caller: Decision(allowed=True, reason="ALLOWED")
```

---

## 3. Effective Permission Formula

$$\mathbf{ALLOW} = \mathbf{I} \land \mathbf{L} \land \mathbf{D} \land \mathbf{E} \land \mathbf{R} \land \mathbf{Q}$$

| Factor | Description | Failure Reason Code |
| :--- | :--- | :--- |
| $\mathbf{I}$ (Identity) | Principal authenticated; zero administrative roles | `ADMIN_ROLE_PROHIBITED` |
| $\mathbf{L}$ (License) | License valid, temporal bounds met, not suspended or revoked | `LICENSE_EXPIRED`, `LICENSE_SUSPENDED`, `LICENSE_REVOKED` |
| $\mathbf{D}$ (Device) | Requesting hardware device registered and active | `DEVICE_INACTIVE` |
| $\mathbf{E}$ (Entitlement) | Feature enabled in policy or active override; permission matches | `FEATURE_NOT_GRANTED`, `PERMISSION_DENIED`, `UNKNOWN_FEATURE` |
| $\mathbf{R}$ (Resource) | Target resource belongs strictly to caller's tenant | `CROSS_TENANT_ACCESS_DENIED` |
| $\mathbf{Q}$ (Quota) | Quota reservation succeeds | `QUOTA_EXCEEDED` |

---

## 4. Fail-Closed Resilience (`ENT-018`)

If an unexpected runtime exception, database timeout, or memory corruption occurs during evaluation:
```python
except Exception as exc:
    logger.error(f"EntitlementService error: {exc}", exc_info=True)
    return self._record_and_return(
        principal=principal,
        feature=norm_feature,
        permission=permission,
        allowed=False,
        reason_code=AuditReasonCode.SERVICE_UNAVAILABLE.value,
        details={"error": str(exc)},
    )
```
The pipeline guarantees that errors result in an immediate deny, preventing bypass via fault injection.
