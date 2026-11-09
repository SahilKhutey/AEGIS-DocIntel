# 02 — Review Queue Specification

## 1. Purpose and Route

- **Route**: `/reviews`
- **Component**: `web/src/features/governance/components/ReviewQueue.tsx`
- **Hook**: `useGovernanceQueue`
- **API Endpoint**: `GET /api/v1/reviews`, `GET /api/v1/reviews/metrics`

The Review Queue serves as the unified inbox for all human governance tasks within the active workspace. It surfaces items requiring human attention, prioritizes them based on model confidence, and enables quick filtering and navigation.

---

## 2. Queue Item Schema

Each item in the queue adheres to the backend `ReviewItem` contract:

```typescript
export interface ReviewItem {
  review_id: string;
  tenant_id: string;
  candidate_id: string;
  candidate_type: "fact" | "conflict";
  document_id: string;
  status: "pending" | "in_review" | "approved" | "corrected" | "rejected" | "needs_evidence";
  version: number;
  assigned_to?: string | null;
  candidate_data: Record<string, unknown>;
  current_revision_id?: string | null;
  current_revision?: ReviewRevision | null;
  created_at: string;
  updated_at: string;
}
```

---

## 3. Filters and Controls

1. **Status Filter Tabs**:
   - `All Items` (with total badge)
   - `Pending` (unclaimed extractions awaiting review)
   - `In Review` (claimed by an active reviewer)
   - `Approved` (verified extractions signed off by human)
   - `Corrected` (human-corrected values with evidence citations)
   - `Rejected` (hallucinations or refuted facts discarded)
   - `Needs Evidence` (items flagged for additional context or re-extraction)

2. **Candidate Type Filter**:
   - `All Types`
   - `Facts Only`
   - `Conflicts Only`

3. **Assignment Filter**:
   - `All Assignments`
   - `Unassigned`
   - `Assigned`

4. **Live Search**:
   - Searches candidate ID, subject, attribute, document ID, and review ID in real time.

---

## 4. Metrics Banner

Renders real-time governance metrics via `GovernanceMetricsBanner`:
- **Total Queue**: Total items in current tenant queue.
- **Approval Rate**: Percentage of decided items approved without modification.
- **Correction Rate**: Percentage of items modified with human ground-truth corrections.
- **Rejection Rate**: Percentage of candidate extractions rejected.

---

## 5. Strict Backward Compatibility

The Review Queue preserves the legacy automated test contract:
- The main heading strictly matches `/human governance review queue/i`.
- Candidate identifiers (e.g., `revenue_q3_2026`) are clearly visible and clickable.
- Links route directly to `/reviews/[reviewId]`.
