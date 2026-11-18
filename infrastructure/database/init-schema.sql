-- AEGIS-DocIntel Logical Database Architecture & Schema Initialization
-- PROT-FINAL-05: Workstream DEP-04

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =========================================================================
-- DOMAIN 1: IDENTITY & EVALUATOR SESSIONS
-- =========================================================================
CREATE TABLE IF NOT EXISTS identity_evaluators (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    email VARCHAR(255) NOT NULL,
    account_status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_evaluators_tenant ON identity_evaluators(tenant_id);

CREATE TABLE IF NOT EXISTS identity_sessions (
    id VARCHAR(64) PRIMARY KEY,
    evaluator_id VARCHAR(64) NOT NULL REFERENCES identity_evaluators(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    token_hash VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON identity_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sessions_evaluator ON identity_sessions(evaluator_id);

-- =========================================================================
-- DOMAIN 2: EVALUATION LICENSES & DEVICES
-- =========================================================================
CREATE TABLE IF NOT EXISTS evaluation_licenses (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    license_key VARCHAR(128) UNIQUE NOT NULL,
    tier VARCHAR(32) NOT NULL DEFAULT 'DEMO',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_licenses_tenant ON evaluation_licenses(tenant_id);

CREATE TABLE IF NOT EXISTS evaluation_devices (
    id VARCHAR(64) PRIMARY KEY,
    license_id VARCHAR(64) NOT NULL REFERENCES evaluation_licenses(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    machine_fingerprint VARCHAR(128) NOT NULL,
    public_key_pem TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_devices_license ON evaluation_devices(license_id);

-- =========================================================================
-- DOMAIN 3: AUTHORIZATION & ENTITLEMENTS
-- =========================================================================
CREATE TABLE IF NOT EXISTS authorization_entitlements (
    id VARCHAR(64) PRIMARY KEY,
    license_id VARCHAR(64) NOT NULL REFERENCES evaluation_licenses(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    feature_name VARCHAR(64) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    revision INT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_entitlements_lic_feat ON authorization_entitlements(license_id, feature_name);

-- =========================================================================
-- DOMAIN 4: USAGE, QUOTAS & RESERVATIONS
-- =========================================================================
CREATE TABLE IF NOT EXISTS usage_quota_counters (
    id VARCHAR(64) PRIMARY KEY,
    license_id VARCHAR(64) NOT NULL REFERENCES evaluation_licenses(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    current_usage INT NOT NULL DEFAULT 0,
    max_limit INT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMPTZ NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_quota_metric ON usage_quota_counters(license_id, metric_name);

CREATE TABLE IF NOT EXISTS usage_reservations (
    id VARCHAR(64) PRIMARY KEY,
    license_id VARCHAR(64) NOT NULL REFERENCES evaluation_licenses(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    amount INT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'RESERVED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reservations_lic ON usage_reservations(license_id);

-- =========================================================================
-- DOMAIN 5: DOCUMENTS & PROCESSING JOBS
-- =========================================================================
CREATE TABLE IF NOT EXISTS documents_metadata (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    license_id VARCHAR(64) NOT NULL REFERENCES evaluation_licenses(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    page_count INT NOT NULL DEFAULT 1,
    storage_path VARCHAR(512) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents_metadata(tenant_id, id);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents_metadata(id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    retry_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON processing_jobs(tenant_id);

-- =========================================================================
-- DOMAIN 6: SECURITY & AUDIT EVENT LEDGER
-- =========================================================================
CREATE TABLE IF NOT EXISTS security_audit_events (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    resource_id VARCHAR(128),
    details JSONB,
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_tenant_time ON security_audit_events(tenant_id, timestamp DESC);
