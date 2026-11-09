# Role-Permission Matrix & Backend RBAC Mapping

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering & Security Architecture |
| Dependencies | `src/core/security_context.py`, `src/api/auth.py`, `src/engines/governance/policy.py` |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Establishes the binding mapping between frontend product personas, granular UI permissions, and the verified backend FastAPI Role-Based Access Control (RBAC) security architecture.

## 2. Granular UI Permissions Vocabulary

| Permission Identifier | Description | Scope |
| :--- | :--- | :--- |
| `workspace.read` | View workspace overview, activity, and metrics | Workspace |
| `documents.read` | View authorized document library, chunks, and metadata | Documents |
| `documents.upload` | Ingest documents via drag-and-drop or S3 manifest | Documents |
| `documents.delete` | Delete documents and trigger cascade cleanup | Documents |
| `documents.compare` | Execute pairwise document comparisons and view conflicts | Intelligence |
| `processing.read` | Monitor background jobs, progress, and stage timings | Processing |
| `intelligence.query` | Formulate natural language inquiries and stream answers | Intelligence |
| `evidence.read` | Inspect source citations, quotes, and bounding boxes | Evidence |
| `governance.read` | Inspect the human governance review queue | Governance |
| `governance.review` | Claim review items and submit binding decisions | Governance |
| `governance.audit.read` | Read tamper-evident cryptographic audit event logs | Governance |
| `users.manage` | Manage workspace users and membership invitations | Admin |
| `workspace.settings.manage` | Update tenant quotas, storage policies, and settings | Admin |
| `integrations.manage` | Manage webhook endpoints, API keys, and external feeds | Developer |

---

## 3. Product Persona to Granular Permission Matrix

| Capability | Workspace User | Analyst | Reviewer | Administrator | Developer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `workspace.read` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `documents.read` | ✓ | ✓ | ✓ | ✓ | — |
| `documents.upload` | ✓ | ✓ | — | ✓ | — |
| `documents.delete` | — | — | — | ✓ | — |
| `documents.compare` | — | ✓ | ✓ | ✓ | — |
| `processing.read` | — | ✓ | ✓ | ✓ | — |
| `intelligence.query` | ✓ | ✓ | ✓ | ✓ | — |
| `evidence.read` | ✓ | ✓ | ✓ | ✓ | — |
| `governance.read` | — | ✓ | ✓ | ✓ | — |
| `governance.review` | — | — | ✓ | ✓* | — |
| `governance.audit.read` | — | — | ✓* | ✓ | — |
| `users.manage` | — | — | — | ✓ | — |
| `workspace.settings.manage` | — | — | — | ✓ | — |
| `integrations.manage` | — | — | — | ✓ | ✓ |

*Proposed product default; requires explicit backend qualification.

---

## 4. Backend RBAC Contract Alignment

The backend FastAPI authority (`src/core/security_context.py` and `src/api/auth.py`) implements canonical enterprise roles. The product-level personas map to the backend roles as follows:

| Product Persona | Canonical Backend Role | Backend Roles Enum | Backend Capabilities |
| :--- | :--- | :--- | :--- |
| **Workspace User** | `viewer` | `ROLE_VIEWER` | Read authorized documents, query RAG. |
| **Intelligence Analyst** | `editor` | `ROLE_EDITOR` | Ingest documents, trigger comparisons, view conflicts. |
| **Governance Reviewer** | `reviewer` | `ROLE_REVIEWER` | Claim items, submit sovereign decisions (`approve`, `correct`, `reject`, `request_evidence`). |
| **Workspace Administrator** | `tenant_admin` / `admin` | `ROLE_TENANT_ADMIN`, `LEGACY_ADMIN` | Quotas, users, API keys, reopen reviews (`ROLE_REVIEW_ADMIN`). |
| **Platform Administrator** | `platform_admin` | `ROLE_PLATFORM_ADMIN` | Global system health, DLQ recovery, cross-tenant telemetry. |
| **Developer / Integrator** | `editor` (API Key) | `ROLE_EDITOR` | API key and webhook operations scoped to tenant. |

### Governance Decision Authorization Policy (`src/engines/governance/policy.py`):
1. **Claim Item**: Caller must hold role `reviewer`, `review_admin`, `admin`, or `tenant_admin`. Item status must be `pending` or `needs_evidence`.
2. **Submit Decision** (`approve`, `correct`, `reject`, `request_evidence`): Caller must hold `reviewer` role and item status must be `in_review`.
3. **Reopen Decision**: Caller must hold `admin`, `tenant_admin`, or `review_admin` role. Item status must be in terminal state (`approved`, `corrected`, `rejected`).

## 5. Security Invariants

- Frontend permission checks (`canAccess`) control UI visibility only.
- The FastAPI backend validates `TenantContext` on every single protected route (`HTTP 401/403`).
- Client state cannot elevate role entitlements or cross tenant boundaries.
