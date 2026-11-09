# 06 — Audit History Specification

## 1. Overview and Routes

- **Item History Route**: `/reviews/[reviewId]` (Tab: "Audit Trail")
- **Deep-Link Route**: `/reviews/[reviewId]/history`
- **Global Workspace Route**: `/governance/audit`
- **Component**: `web/src/features/governance/components/AuditTimeline.tsx`

The Audit History system delivers an immutable, append-only chronological record of all actions, version mutations, state changes, actor identities, and justifications throughout the review lifecycle.

---

## 2. Audit Event Schema

Every transition creates an `AuditEvent` adhering to backend contracts:

```typescript
export interface AuditEvent {
  event_id: string;
  review_id: string;
  sequence: number;           // 1-based monotonic integer
  tenant_id: string;
  actor_id: string;           // Authenticated user ID
  action: string;             // create, claim, approve, correct, reject, etc.
  previous_status: string;
  new_status: string;
  previous_version: number;
  new_version: number;
  rationale: string;
  revision_id?: string | null;
  request_id?: string | null;
  timestamp: string;          // ISO 8601 UTC
}
```

---

## 3. Visual Presentation & Sorting

The timeline table displays:
1. **Sequence ID**: Monotonic sequence (e.g. `#1`, `#2`, `#3`).
2. **Timestamp**: Localized date and time with second precision.
3. **Actor**: Identity of the user or system worker.
4. **Action**: Color-coded pill (`Created`, `Claimed`, `Approved`, `Corrected`, `Rejected`, `Evidence Requested`, `Reopened`).
5. **Status Transition**: `previous_status -> new_status`.
6. **Version Transition**: `vPrevious -> vNew`.
7. **Audited Rationale**: The exact textual rationale entered by the human actor.

### Chronological Sorting
Users can toggle between:
- **Newest First (Descending)**: Quick inspection of the latest action.
- **Oldest First (Ascending)**: Step-by-step audit reconstruction from initial creation.

---

## 4. Global Workspace Audit Log (`/governance/audit`)

In addition to per-item history, `/governance/audit` aggregates all review audit logs across the workspace. It features:
- Filter by action (`approve`, `correct`, `reject`, `request_evidence`, `claim`, `reopen`).
- Search by review ID, candidate identifier, actor ID, or rationale text.
- Direct links to parent review items.
