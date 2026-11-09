# WP-UI-06: Governance Workspace

## 1. Executive Summary

The **Governance Workspace** delivers the human oversight layer for **AEGIS-DocIntel**.

> **Core Principle**: AI models ingest documents, retrieve passages, and propose candidate extractions; source evidence passages provide evidentiary support; **authorized humans make binding governance decisions**.

This work package establishes an enterprise-grade human-in-the-loop (HITL) review system with strict concurrency controls, tamper-evident audit logging, grounded fact verification, cross-document conflict resolution, and quality evaluation feedback loops.

---

## 2. Five Core Capabilities Delivered

1. **Review Queue (`/reviews`)**:
   - Centralized queue for candidate facts and cross-document conflicts awaiting human inspection.
   - Comprehensive status tabs (`all`, `pending`, `in_review`, `approved`, `corrected`, `rejected`, `needs_evidence`), candidate type filters (`fact`, `conflict`), assignment filters, and real-time query search.
   - Live governance metrics banner: Total Queue, Approval Rate, Correction Rate, Rejection Rate.
   - Strict backward compatibility preserving legacy automated test expectations (`revenue_q3_2026`).

2. **Fact Verification (`/reviews/[reviewId]/verification` & Tab)**:
   - Deep inspection of extracted statements against grounded source document quotes, page numbers, and model confidence scores.
   - Standardized verification outcomes: `verified`, `partially_verified`, `not_verified`, `contradicted`, `insufficient_evidence`.
   - Dynamic prompt for corrected value when statements are partially verified.

3. **Conflict Resolution (`/reviews/[reviewId]/conflicts` & Tab)**:
   - Side-by-side comparative inspection of contradictory assertions across multiple source documents.
   - Evaluates provenance, publishing date, and GAAP/audited standing.
   - Resolution outcomes: `accepted_first_fact`, `accepted_second_fact`, `both_valid` (with reconciled value), `insufficient_evidence`, `escalated`.

4. **Decision Management (`/reviews/[reviewId]/decisions` & Tab)**:
   - Formal state machine execution: `approve`, `correct`, `reject`, `request_evidence`.
   - Concurrency control with `expected_version` and stale version conflict detection (HTTP 409).
   - Idempotency key tracking via `Idempotency-Key` headers.
   - Item claiming (`claimReviewItem`) and administrative reopen (`reopenReviewItem`) workflows.
   - Mandatory reviewer rationale and compliance certification safeguard checkbox.

5. **Audit History (`/reviews/[reviewId]/history` & `/governance/audit`)**:
   - Append-only, immutable audit trail of state transitions (`previous_status -> new_status`, `vPrev -> vNew`, actor attribution, timestamp, audited rationale).
   - Global governance audit log (`/governance/audit`) across all workspace reviews with search and action filtering.
   - Diagnostic feedback loop for model evaluations and fine-tuning datasets (`/feedback`).

---

## 3. Specification Index

- [`01-governance-workspace-overview.md`](./01-governance-workspace-overview.md) — High-level functional architecture & goals.
- [`02-review-queue-specification.md`](./02-review-queue-specification.md) — Review queue design, filtering, and metrics.
- [`03-fact-verification-specification.md`](./03-fact-verification-specification.md) — Fact verification panel and citation matching.
- [`04-conflict-resolution-specification.md`](./04-conflict-resolution-specification.md) — Cross-document contradiction resolution.
- [`05-decision-management-specification.md`](./05-decision-management-specification.md) — Formal decision execution & concurrency controls.
- [`06-audit-history-specification.md`](./06-audit-history-specification.md) — Tamper-evident audit timeline & global audit log.
- [`07-state-machine-and-transitions.md`](./07-state-machine-and-transitions.md) — State machine rules & valid transitions.
- [`08-concurrency-and-version-control.md`](./08-concurrency-and-version-control.md) — Optimistic locking and idempotency.
- [`09-human-oversight-and-compliance.md`](./09-human-oversight-and-compliance.md) — Human authority safeguards and sign-offs.
- [`10-component-architecture.md`](./10-component-architecture.md) — Frontend component hierarchy and hooks.
- [`11-route-register-and-navigation.md`](./11-route-register-and-navigation.md) — Route register and deep-link specification.
- [`12-api-integration-mapping.md`](./12-api-integration-mapping.md) — FastAPI endpoint mappings and data contracts.
- [`13-accessibility-and-responsive-design.md`](./13-accessibility-and-responsive-design.md) — WCAG 2.2 AA adherence and mobile support.
- [`14-test-strategy-and-traceability.md`](./14-test-strategy-and-traceability.md) — Test plan, Vitest suites, and Playwright specs.
- [`15-security-and-authorization.md`](./15-security-and-authorization.md) — RBAC separation of duties and tenant isolation.
- [`16-quality-feedback-and-evaluation-loop.md`](./16-quality-feedback-and-evaluation-loop.md) — Diagnostic feedback loop and metrics.
- [`17-implementation-and-execution-log.md`](./17-implementation-and-execution-log.md) — Full execution chronology and verification results.
- [`backend-gap-register.md`](./backend-gap-register.md) — Verified backend contracts vs planned capabilities.
