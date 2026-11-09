# AEGIS-DocIntel — User Personas, Roles & Access Control
**Document Identifier**: `AEGIS-DOCINTEL-UX-ROL-001`  
**Work Package**: `WP-UI-01: Product UX Architecture`  
**Version**: `2.0.0`  
**Classification**: Product & Security Specification  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Role-Based Access Control (RBAC) Framework

AEGIS Workbench 2.0 enforces strict enterprise role-based authorization across all frontend views, interactive components, and mutation triggers. The frontend authorization layer coordinates with backend JWT claims and tenant-scoped security policies.

### 1.1 Standard System Roles

| Role Key | Role Display Name | Primary Scope | Security Clearance |
| :--- | :--- | :--- | :--- |
| `system_admin` | Global System Administrator | Cross-Tenant / Platform | Superuser: System health, DLQ recovery, infrastructure telemetry. |
| `tenant_admin` | Tenant Administrator | Tenant Organization | Tenant-wide settings, user management, API keys, quota allocations. |
| `knowledge_engineer` | Knowledge & Intelligence Engineer | Tenant Datastores | Pipeline tuning, chunking configurations, mathematical topologies, graphs. |
| `compliance_reviewer` | Compliance & Governance Reviewer | Tenant Review Queues | Sovereign decision-making: Approve, Correct, Reject candidate facts & conflicts. |
| `analyst` | Due Diligence & Research Analyst | Tenant Workspace | Document exploration, grounded Ask AEGIS queries, cross-document comparison. |
| `api_developer` | AI Integration Engineer | Developer Subsystem | Webhook management, SDK integration, export package configurations. |

---

## 2. Detailed User Persona Profiles

### Persona 1: Dr. Elena Rostova — Lead Knowledge Engineer & Data Scientist
* **Age**: 39 | **Organization**: Global BioPharma Research Labs
* **Background**: Ph.D. in Computational Linguistics; 12 years building knowledge extraction systems.
* **Core Responsibilities**:
  * Oversees ingestion and mathematical grounding of thousands of clinical trial protocols, patent filings, and chemistry reports.
  * Tunes chunking strategies, embedding models, and topological graph extraction to ensure zero omission of adverse drug reactions.
* **Pain Points & Frustrations**:
  * Black-box LLM systems that summarize without providing layout coordinates or token provenance.
  * Lack of visibility into pipeline failures (e.g., table extraction silently collapsing multi-span headers).
* **Mental Model**: Views documents as multidimensional mathematical graphs of assertions, entities, and empirical measurements.
* **Essential UI Needs**:
  * Pipeline Monitor with step-level timings and failure diagnostics.
  * Document Chunk & Layout Inspector showing bounding boxes and reading order.
  * Knowledge Graph Visualizer and Ising Annealing Parameter Sandbox.
* **Success Metric**: 99.8% extraction recall across dense scientific tables with sub-second retrieval latency.

---

### Persona 2: Marcus Vance — Senior Compliance Officer & Legal Reviewer
* **Age**: 47 | **Organization**: Tier-1 International Investment Bank & Asset Management
* **Background**: J.D. in Corporate Securities Law; 18 years in regulatory compliance and risk management.
* **Core Responsibilities**:
  * Reviews credit agreements, bond indentures, and regulatory disclosures for conflicting covenants or misstated financial metrics.
  * Validates AI-extracted facts and makes legally binding decisions on contested assertions.
* **Pain Points & Frustrations**:
  * Systems that make confident claims without direct, verifiable proof in the source document.
  * Cumbersome review interfaces requiring constant alt-tabbing between separate PDF viewers and forms.
  * Audit logs that fail to document who changed what value and why.
* **Mental Model**: "Trust, but verify with a tamper-evident audit trail."
* **Essential UI Needs**:
  * Dedicated Review Queue with fast keyboard triage (`J`/`K` navigation, `A` approve, `C` correct).
  * Synchronized Split-Pane PDF Canvas highlighting vector bounding boxes for evidence quotes.
  * Cryptographically anchored audit trail showing all previous revisions and actor rationales.
* **Success Metric**: 100% auditable sign-off on regulatory filings with zero undetected cross-document contradictions.

---

### Persona 3: Sarah Chen — M&A Due Diligence & Financial Analyst
* **Age**: 28 | **Organization**: Strategic Private Equity & Advisory
* **Background**: B.S. in Financial Engineering; 5 years executing complex buy-side technology acquisitions.
* **Core Responsibilities**:
  * Rapidly analyzes data rooms containing 5,000+ contracts, supplier master services agreements (MSAs), and financial spreadsheets.
  * Answers critical deal questions: "Which agreements contain Change of Control clauses with termination penalties?"
* **Pain Points & Frustrations**:
  * Wasting 15 hours manually cross-referencing definitions across 40 related deal documents.
  * Chatbots that hallucinate subtle clauses or omit unfavorable terms under pressure.
* **Mental Model**: Needs rapid, high-confidence synthesis with instant proof links for investment committee memos.
* **Essential UI Needs**:
  * Tri-pane "Ask AEGIS" query console with real-time answer streaming and citation badges.
  * Cross-Document Comparison Console with automated contradiction matrix.
  * Exportable context packages formatted for executive presentations.
* **Success Metric**: 70% reduction in contract review cycle time during intense 7-day due diligence sprints.

---

### Persona 4: Devraj Patel — Enterprise Security Architect & System Administrator
* **Age**: 44 | **Organization**: Enterprise Cloud Infrastructure Operations
* **Background**: M.S. in Cybersecurity; CISSP certified; 15 years managing regulated cloud deployments.
* **Core Responsibilities**:
  * Enforces multi-tenant data boundaries, tenant encryption isolation, and access credentials.
  * Monitors operational job throughput, worker pool health, and dead-letter queues.
* **Pain Points & Frustrations**:
  * Leaked development tokens, hardcoded credentials, and missing tenant headers in frontend code.
  * Uncontrolled API consumption driving unexpected LLM inference costs.
* **Mental Model**: Strict zero-trust defense-in-depth with real-time telemetry.
* **Essential UI Needs**:
  * Operational Overview Dashboard displaying worker queues, latencies, and token burn rates.
  * Dead-letter queue (DLQ) diagnostic viewer with one-click job retry and cancellation.
  * Scoped API key generator and tenant isolation audit logs.
* **Success Metric**: Zero multi-tenant data bleed incidents, 99.99% system availability, and strictly audited access.

---

### Persona 5: Alex Thorne — AI Integration Engineer & Developer
* **Age**: 31 | **Organization**: Enterprise ISV Partner Ecosystem
* **Background**: Full-stack engineer specializing in TypeScript, Python, and event-driven microservices.
* **Core Responsibilities**:
  * Connects external enterprise applications (Salesforce, SAP, internal ERPs) to AEGIS via REST APIs and webhooks.
  * Consumes verified context packages and feeds them into downstream agentic workflows.
* **Pain Points & Frustrations**:
  * Incomplete API documentation and mismatches between UI representations and backend schemas.
  * Lack of webhook testing utilities and payload delivery verification.
* **Mental Model**: Documents are data feeds that must integrate smoothly via clean, strongly typed API contracts.
* **Essential UI Needs**:
  * Interactive API Explorer and OpenAPI contract inspector.
  * Outbound Webhook Subscription Manager with test-event dispatch and delivery log inspection.
  * LLM-optimized structured export generators (`/v1/advanced/export/llm-optimized`).
* **Success Metric**: Zero-friction SDK and webhook integration with complete end-to-end type safety.

---

## 3. Permissions & Role Capabilities Matrix

The following matrix defines exact access rights per feature area.  
**Legend**:  
* `FULL`: Can view, create, edit, delete, and execute actions.
* `VIEW`: Read-only access to view data and search.
* `ACTION`: Can trigger specific operational workflows (e.g. claim review, ask question).
* `NONE`: Route/Component is hidden and blocked from access.

| Workspace Area / Feature | `system_admin` | `tenant_admin` | `knowledge_engineer` | `compliance_reviewer` | `analyst` | `api_developer` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Operational Overview (`/`)** | FULL (Global) | FULL (Tenant) | FULL (Tenant) | VIEW (Metrics) | VIEW (Workspace) | VIEW (System) |
| **Document Library (`/documents`)** | FULL | FULL | FULL | VIEW | FULL | VIEW |
| **Document Upload & Batch Ingestion** | FULL | FULL | FULL | NONE | FULL | FULL |
| **Document Deletion & Reindexing** | FULL | FULL | FULL | NONE | NONE | NONE |
| **Pipeline Monitor & Jobs (`/processing`)**| FULL | FULL | FULL | VIEW | VIEW | VIEW |
| **Job Cancellation & DLQ Retry** | FULL | FULL | FULL | NONE | NONE | NONE |
| **Ask AEGIS Grounded QA (`/ask`)** | FULL | FULL | FULL | FULL | FULL | FULL |
| **Evidence Studio & Bounding Box** | FULL | FULL | FULL | FULL | FULL | FULL |
| **Compare & Contradictions (`/compare`)**| FULL | FULL | FULL | FULL | FULL | VIEW |
| **Review Queue (`/reviews`)** | FULL | FULL | VIEW | FULL | VIEW | NONE |
| **Submit Sovereign Review Decision** | FULL | FULL | NONE | FULL | NONE | NONE |
| **Reopen Completed Review** | FULL | FULL | NONE | NONE | NONE | NONE |
| **Advanced Math & Topology (`/advanced`)**| FULL | VIEW | FULL | NONE | VIEW | FULL |
| **Analytics & Token Economy (`/analytics`)**| FULL | FULL | VIEW | VIEW | VIEW | VIEW |
| **API Keys & Webhooks (`/admin`)** | FULL | FULL | NONE | NONE | NONE | FULL |
| **Tenant Switcher Context** | Global Scope | Tenant Scope | Tenant Scope | Tenant Scope | Tenant Scope | Tenant Scope |

---

## 4. Multi-Tenant Session Context & Guard Rails

1. **Strict Context Binding**: The active tenant identifier is embedded into the application state upon login and sent via the `X-Tenant-ID` or JWT claims in every API request.
2. **Tenant Switching**: Users assigned to multiple tenants (e.g., consultants or system admins) must explicitly select their active tenant from the header dropdown. All cache keys in TanStack Query are tagged with the active tenant ID to prevent cross-tenant data caching.
3. **Session Invalidation**: When switching tenants or logging out, the client completely clears the in-memory cache, resets active document states, and refreshes the navigation hierarchy.
