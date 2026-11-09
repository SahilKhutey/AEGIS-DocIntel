# Backend Gap Register: WP-UI-06 Governance Workspace

## 1. Overview

In accordance with the project implementation principle:
> *Every screen and interaction must map to an existing API capability, or be explicitly marked as a planned feature. Do not invent backend capabilities.*

This register documents the verified backend contracts in FastAPI against planned future enterprise capabilities.

---

## 2. Verified Operational Capabilities

| Capability | Backend Endpoint | Contract Source | Status in UI |
| :--- | :--- | :--- | :--- |
| Review Queue Listing | `GET /v1/reviews` | `contracts/openapi.yaml` | Fully Integrated |
| Review Queue Metrics | `GET /v1/reviews/metrics` | `contracts/openapi.yaml` | Fully Integrated |
| Item Detail Retrieval | `GET /v1/reviews/{id}` | `src/engines/governance/contracts.py` | Fully Integrated |
| Claim Review Item | `POST /v1/reviews/{id}/claim` | `src/engines/governance/review_service.py` | Fully Integrated |
| Submit Decision | `POST /v1/reviews/{id}/decisions` | `src/engines/governance/review_service.py` | Fully Integrated |
| Administrative Reopen | `POST /v1/reviews/{id}/reopen` | `src/engines/governance/review_service.py` | Fully Integrated |
| Append-Only Audit Trail | `GET /v1/reviews/{id}/history` | `src/engines/governance/contracts.py` | Fully Integrated |
| Evaluation Feedback Loop | `POST /v1/reviews/{id}/feedback` | `src/engines/governance/feedback.py` | Fully Integrated |

---

## 3. Identified Gaps & Planned Enhancements

### Gap 1: Global Workspace Audit Search Endpoint
- **Current State**: `GET /v1/reviews/{id}/history` retrieves audit events per review item. To view the global workspace audit log, the frontend aggregates audit trails across active reviews.
- **Planned Backend Enhancement**: Provide a dedicated `GET /v1/governance/audit` endpoint supporting cursor-based pagination and tenant-wide actor/action filtering.
- **Frontend Mitigation**: Fully implemented client-side aggregation and filtering in `web/src/app/governance/audit/page.tsx` without inventing unauthorized endpoints.

### Gap 2: Batch Decision Submission
- **Current State**: Decisions are committed per-review item to ensure version concurrency and explicit actor attribution.
- **Planned Backend Enhancement**: Implement `POST /v1/reviews/batch-decisions` with transactional rollback if any expected version conflicts.
- **Frontend Mitigation**: Batch review UI is deferred to preserve atomic version verification per item.

### Gap 3: WebSocket / SSE Live Queue Push
- **Current State**: Queue updates occur via polling or user-initiated "Refresh Queue".
- **Planned Backend Enhancement**: Server-Sent Events (SSE) channel at `/v1/reviews/stream` notifying reviewers of new incoming extractions or claims in real time.
- **Frontend Mitigation**: "Refresh Queue" action provided in header with subtle indicator.
