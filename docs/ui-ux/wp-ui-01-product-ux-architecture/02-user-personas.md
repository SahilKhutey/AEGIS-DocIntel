# User Personas & Organizational Archetypes

| Field | Value |
|---|---|
| Project | AEGIS-DocIntel |
| Work Package | WP-UI-01 |
| Version | 1.0.0 |
| Status | Approved |
| Owner | Product Engineering |
| Dependencies | Existing web application, FastAPI, OpenAPI |
| Last Verified Commit | ee293f0 |
| Review Date | 2026-11-09 |

---

## 1. Purpose

Defines the five target enterprise personas interacting with AEGIS-DocIntel, establishing their operational responsibilities, mental models, pain points, and primary product journeys.

## 2. Scope

Defines product-level personas: Workspace User, Intelligence Analyst, Governance Reviewer, Workspace Administrator, and Developer / Integrator.

## 3. Persona Profiles

### Persona A: Workspace User
- **Role Key**: `workspace_user`
- **Primary Responsibility**: Upload, locate, and understand authorized documents.
- **Main Screens**: Overview (`/`), Document Library (`/documents`), Ask AEGIS (`/ask`).
- **Core Goals**: Fast search, reliable ingestion status, straightforward fact lookups.
- **Access Boundary**: Can upload and read authorized documents; cannot approve governance decisions.

### Persona B: Intelligence Analyst
- **Role Key**: `analyst`
- **Primary Responsibility**: Deeply investigate documents, cross-reference clauses, and detect discrepancies.
- **Main Screens**: Document Library (`/documents`), Ask AEGIS (`/ask`), Document Comparison (`/compare`).
- **Core Goals**: Grounded multi-hop QA, side-by-side contradiction matrix, citation verification.
- **Access Boundary**: Can query and compare authorized documents; cannot bypass review queues.

### Persona C: Governance Reviewer
- **Role Key**: `reviewer`
- **Primary Responsibility**: Verify candidate facts and conflicts against source evidence, formulate binding decisions.
- **Main Screens**: Review Queue (`/reviews`), Review Details (`/reviews/[reviewId]`), Document Viewer.
- **Core Goals**: Side-by-side evidence inspection, rapid keyboard triage (`J`/`K`), mandatory rationale entry.
- **Access Boundary**: Authorized to claim and decide review items; cannot reconfigure system settings.

### Persona D: Workspace Administrator
- **Role Key**: `administrator`
- **Primary Responsibility**: Administer workspace users, tenant quotas, security keys, and worker infrastructure.
- **Main Screens**: Overview (`/`), Settings (`/settings`), Processing Monitor (`/processing`).
- **Core Goals**: Multi-tenant isolation oversight, quota management, failure recovery.
- **Access Boundary**: Manages workspace configuration; cannot approve review decisions without reviewer qualification.

### Persona E: Developer / Integrator
- **Role Key**: `developer`
- **Primary Responsibility**: Integrate AEGIS into external enterprise systems (CRM, ERP, legal repositories).
- **Main Screens**: Integrations (`/integrations`), API Explorer, Webhooks.
- **Core Goals**: OpenAPI contract inspection, webhook delivery verification, export package assembly.
- **Access Boundary**: Scoped to developer tools and authorized API credentials within assigned tenants.

## 4. Approval & Change History

- **v1.0.0 (2026-11-09)**: Personas standardized for WP-UI-01 baseline.
