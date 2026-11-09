# 09 — External Integrations and Connectors

## 1. Functional Scope
The Integrations Interface (`IntegrationStatusCard.tsx`, `/developer/integrations`) surfaces connection health, verified endpoints, and test ping diagnostics for backing infrastructure.

## 2. Integrated Services
1. **Object Storage**:
   - Provider: AWS S3 / Cloudflare R2
   - Role: Preserves raw multi-page PDF/DOCX binaries and OCR bounding-box snapshots.
2. **Metadata Store**:
   - Provider: PostgreSQL 16
   - Role: Tracks tenant tenancy, document manifests, review candidates, and tamper-evident audit logs.
3. **Vector Search Cluster**:
   - Provider: Qdrant / Milvus (Distributed HNSW)
   - Role: Stores 1536-dimensional semantic chunk embeddings for sub-200ms hybrid search.
4. **Enterprise Identity & SSO**:
   - Provider: OIDC / Okta / Azure AD
   - Role: Enforces workspace RBAC roles and authenticates reviewer identities.
