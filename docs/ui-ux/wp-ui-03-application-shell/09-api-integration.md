# 09 — API Capability Mapping & Backend Truth

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-09`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Backend Architecture Reality

The backend integration baseline is strictly defined by the FastAPI OpenAPI 3.1 specification (`contracts/openapi.yaml`) and the API Endpoint Inventory (`contracts/API_ENDPOINT_INVENTORY.csv`).

Every UI capability proposed in WP-UI-03 was audited against verified endpoints. Capabilities lacking dedicated backend endpoints are documented with complete transparency:

```
+-----------------------------------------------------------------------------------------------+
| FRONTEND SHELL CAPABILITY       | BACKEND REALITY (FastAPI)           | INTEGRATION STATUS    |
+---------------------------------+-------------------------------------+-----------------------+
| Workspace Switcher              | Session header (X-Tenant-ID) / JWT  | CONTEXTUAL CLIENT     |
|                                 | No /v1/workspaces endpoint          | Display-only context  |
+---------------------------------+-------------------------------------+-----------------------+
| Notification Center (Push/Read) | Event logs in /v1/jobs & /v1/reviews| BLOCKED (PUSH/READ)   |
|                                 | No /v1/notifications endpoint       | State mapped from jobs|
+---------------------------------+-------------------------------------+-----------------------+
| Global Search                   | /v1/documents & /v1/query endpoints | PARTIAL               |
|                                 | No omnibus /v1/search endpoint      | Query mapping enabled |
+---------------------------------+-------------------------------------+-----------------------+
```

---

## 2. Capability Audit & Endpoint Mapping

| UI Shell Feature | Proposed Action | Backend Endpoint Status | Handling Strategy |
| :--- | :--- | :--- | :--- |
| **Workspace Listing** | List available workspaces | NO dedicated endpoint (`/v1/workspaces` does not exist) | Managed via authenticated profile context or configuration. |
| **Workspace Switch** | Switch tenant context | Enforced via `X-Tenant-ID` header per request | Trigger page reload or tenant context change; client never simulates fake auth tokens. |
| **Notification Center**| Fetch alerts & mark read | NO dedicated endpoint (`/v1/notifications` does not exist) | Documented as **BLOCKED**. Components accept live job/review metrics via props. |
| **Job Progress Alerts**| Track document ingestion | Verified: `GET /v1/jobs/{job_id}` | Supported via durable job polling. |
| **Review Queue Alerts**| Alert on pending reviews | Verified: `GET /v1/reviews` | Supported via governance review queue querying. |
| **Global Search** | Omni-entity query | NO omnibus `/v1/search` endpoint | Maps queries to `GET /v1/documents` and `POST /v1/query`. |
| **User Sign Out** | Revoke session | Enforced by client token clearing or IdP | Trigger sign-out callback. |

---

## 3. Strict Prohibitions

1. **NO Synthetic Success**: Never display "Notification marked as read in database" when no backend write endpoint exists.
2. **NO Hardcoded `default-tenant` Fallbacks**: Multi-tenancy must always require explicit credentials or configuration.
3. **NO Developer Token Bypasses**: Never bypass authentication headers in production code.
