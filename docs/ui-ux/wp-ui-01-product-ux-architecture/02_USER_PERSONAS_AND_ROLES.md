# AEGIS-DocIntel — User Personas, Roles & Access Control

## 1. Initial Product Personas

These personas represent primary operational archetypes interacting with AEGIS Workbench 2.0:

| Persona | Primary Objective | Main Screens | Typical User Role |
| :--- | :--- | :--- | :--- |
| **Workspace User** | Ingest, browse, and search document libraries; ask grounded questions. | Overview, Documents, Ask AEGIS | Standard User |
| **Analyst** | Deeply investigate evidence, compare multi-document agreements, detect contradictions. | Ask, Compare, Evidence Explorer | Analyst |
| **Reviewer** | Triage governance queue, verify candidate facts, formulate binding decisions, record rationale. | Review Queue, Review Details | Compliance Reviewer |
| **Administrator** | Manage tenants, users, quotas, system health, worker pools, and API keys. | Overview, Settings, Admin, Jobs | Tenant / System Admin |
| **Developer / Integrator**| Connect enterprise data systems via REST APIs, webhooks, and SDK context packages. | Developer Hub, Webhooks, API Docs | Integration Engineer |

## 2. Required Authorization Matrix

The frontend authorization layer enforces explicit boundaries aligned with backend security policies.

| Capability | Workspace User | Analyst | Reviewer | Administrator |
| :--- | :---: | :---: | :---: | :---: |
| **Read authorized documents** | Verify | Verify | Verify | Verify |
| **Upload documents** | Verify | Verify | Verify | Verify |
| **Delete documents** | No | No | No | Verify |
| **Run intelligence queries** | Verify | Verify | Verify | Verify |
| **Compare documents** | Verify | Verify | Verify | Verify |
| **Inspect evidence bounding boxes** | Verify | Verify | Verify | Verify |
| **Submit governance decisions** | No by default | No by default | Verify | Verify |
| **Claim review items** | No | No | Verify | Verify |
| **Reopen finalized reviews** | No | No | No | Verify |
| **Retry / cancel processing jobs** | No | No | No | Verify |
| **Manage users & tenant quotas** | No | No | No | Verify |
| **Manage webhook subscriptions** | No | No | No | Verify |

> **Security Rule**: "Verify" requires validating against the authenticated user's session claims and active tenant context before exposing or executing actions. The frontend must never infer permissions merely from client-side role names.

## 3. Persona Scenarios & Workflow Needs

1. **Dr. Elena Rostova (Knowledge Engineer)**: Demands transparency into OCR, layout boundaries, and reading order graphs. Requires immediate visibility into parsing failures without silent dropouts.
2. **Marcus Vance (Compliance Reviewer)**: Requires an ergonomic review interface with side-by-side evidence inspection, fast keyboard triage (`J`/`K`), and immutable audit trail verification.
3. **Sarah Chen (Due Diligence Analyst)**: Requires grounded multi-hop answering with interactive citation badges and cross-document contradiction matrices.
4. **Devraj Patel (System Administrator)**: Requires live pipeline telemetry, worker health metrics, dead-letter queue (DLQ) diagnostics, and scoped API key management.
