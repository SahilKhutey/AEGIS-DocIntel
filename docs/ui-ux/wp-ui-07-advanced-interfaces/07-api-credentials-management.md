# 07 — API Credentials Management

## 1. Functional Scope
The API Credentials interface (`ApiCredentialManager.tsx`) manages programmatic Bearer tokens for external microservices and enterprise ETL workflows.

## 2. Security Lifecycle
```mermaid
sequenceDiagram
    autonumber
    actor Admin as Workspace Administrator
    participant UI as API Credential Manager
    participant Backend as FastAPI Auth Router
    participant DB as Hashed Storage

    Admin->>UI: Request new key (name, scopes)
    UI->>Backend: POST /v1/auth/keys
    Backend->>DB: Store SHA-256 key hash
    Backend-->>UI: Return key prefix + one-time secret
    UI->>Admin: Display secret in prominent alert banner
    Admin->>Admin: Store secret in secure vault
    Admin->>UI: Dismiss banner ("Stored safely")
    Note over UI: Secret purged from memory; never retrievable
```

## 3. Strict Safety Invariants
1. **Masked Metadata**: Only the prefix (`aegis_live_****3fa9`) is persisted in the UI state.
2. **One-Time Secret Banner**: Secrets are presented once at generation time and never logged or written to localStorage.
3. **Instant Revocation**: Revoking a credential immediately invalidates all active sessions bound to the key ID.
