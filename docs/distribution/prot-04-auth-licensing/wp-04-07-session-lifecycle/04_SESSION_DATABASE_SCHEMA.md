# Dossier 04: Session Authoritative Database Schema

**Work Package:** PROT-04.07  
**Module:** `AEGIS-DocIntel Database & Repository Schemas`  
**Status:** **PASSED / CERTIFIED & SIGNED OFF**

---

## 1. Relational Schema Architecture

```sql
-- Authoritative Evaluation Sessions Table
CREATE TABLE evaluation_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    evaluator_id VARCHAR(128) NOT NULL,
    tenant_id VARCHAR(128) NOT NULL,
    license_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active', -- active, revoked, expired, suspended
    token_family_id VARCHAR(64) NOT NULL,
    access_token_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,
    idle_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    absolute_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason VARCHAR(64),
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_eval_sessions_evaluator ON evaluation_sessions(evaluator_id);
CREATE INDEX idx_eval_sessions_device ON evaluation_sessions(device_id);
CREATE INDEX idx_eval_sessions_license ON evaluation_sessions(license_id);
CREATE INDEX idx_eval_sessions_family ON evaluation_sessions(token_family_id);

-- Authoritative Refresh Tokens Table (Hashes Only)
CREATE TABLE evaluation_refresh_tokens (
    token_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES evaluation_sessions(session_id) ON DELETE CASCADE,
    family_id VARCHAR(64) NOT NULL,
    token_hash CHAR(64) NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'active', -- active, consumed, revoked, expired
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    consumed_at TIMESTAMP WITH TIME ZONE,
    replaced_by_id VARCHAR(64) REFERENCES evaluation_refresh_tokens(token_id),
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason VARCHAR(64)
);

CREATE INDEX idx_eval_refresh_family ON evaluation_refresh_tokens(family_id);
CREATE INDEX idx_eval_refresh_status ON evaluation_refresh_tokens(status);

-- Immutable Session Audit Ledger Table
CREATE TABLE evaluation_session_audit (
    event_id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    session_id VARCHAR(64),
    evaluator_id VARCHAR(128),
    license_id VARCHAR(64),
    device_id VARCHAR(64),
    status VARCHAR(32) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_eval_audit_timestamp ON evaluation_session_audit(timestamp);
CREATE INDEX idx_eval_audit_evaluator ON evaluation_session_audit(evaluator_id);
```

---

## 2. In-Memory Thread-Safe Indexes

In ephemeral evaluation gateway deployments, the schemas are maintained in-memory using bidirectional hash indexes:
- `_sessions: Dict[str, EvaluationSession]` (O(1) session lookups)
- `_access_hash_index: Dict[str, str]` (O(1) bearer validation)
- `_family_index: Dict[str, Set[str]]` (O(1) compromise cascade)
- `_evaluator_index: Dict[str, Set[str]]` (O(1) logout-all cascade)
- `_device_index: Dict[str, Set[str]]` (O(1) deactivation cascade)
- `_license_index: Dict[str, Set[str]]` (O(1) license revocation cascade)
