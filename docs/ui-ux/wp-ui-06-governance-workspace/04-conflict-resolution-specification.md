# 04 — Conflict Resolution Specification

## 1. Overview and Route

- **Primary Route**: `/reviews/[reviewId]` (Tab: "Conflict Resolution")
- **Deep-Link Route**: `/reviews/[reviewId]/conflicts`
- **Component**: `web/src/features/governance/components/ConflictResolutionPanel.tsx`

When the backend cross-document contradiction detection engine identifies incompatible statements for the same subject and attribute across multiple source documents, it creates a `candidate_type: "conflict"` review item.

The Conflict Resolution Panel enables human experts to inspect both conflicting claims side-by-side, assess their provenance, and record a binding resolution.

---

## 2. Side-by-Side Comparative UI

```
+-----------------------------------------------------------------------------------+
| [CONFLICT INVESTIGATION]  Acme Corporation • ebitda_margin_q3                     |
+--------------------------------------------------+--------------------------------+
| CLAIM 1 (SOURCE A)                               | CLAIM 2 (SOURCE B)             |
| Document: doc-alpha-001                          | Document: doc-alpha-002        |
| Asserted Value: 22.5%                            | Asserted Value: 24.1%          |
| Source Passage:                                  | Source Passage:                |
| "Preliminary shareholder deck reported EBITDA    | "Certified 10-Q financial      |
|  margin of 22.5%."                               |  filing confirmed EBITDA 24.1%"|
| [Inspect Source A ->]                            | [Inspect Source B ->]          |
+--------------------------------------------------+--------------------------------+
| CONFLICT RESOLUTION OUTCOMES:                                                     |
| [ Accept Fact 1 (Source A) ]    [ Accept Fact 2 (Source B) ]                      |
| [ Reconcile / Both Valid ]      [ Insufficient Evidence ]                         |
| [ Escalate for Compliance Review ]                                                |
|                                                                                   |
| Resolution Rationale (min 5 chars required):                                      |
| [ Textarea: Justify resolution based on GAAP standards, recency, etc...          ] |
|                                                                                   |
|                                         [ Commit Conflict Resolution -> ]         |
+-----------------------------------------------------------------------------------+
```

---

## 3. Resolution Outcomes

1. **`accepted_first_fact`**:
   - Source A supersedes Source B (e.g., later amendment or authoritative source).
   - Maps to decision `approve` using Fact 1's value and quote.
2. **`accepted_second_fact`**:
   - Source B supersedes Source A (e.g., audited 10-K supersedes unaudited press release).
   - Maps to decision `correct` using Fact 2's value and quote.
3. **`both_valid`**:
   - Discrepancy is temporal, geographical, or accounting basis divergence.
   - Prompts for a human reconciled/qualified value (e.g., "GAAP: 24.1%, Non-GAAP: 22.5%").
   - Maps to decision `correct` with reconciled value.
4. **`insufficient_evidence`**:
   - Discrepancy cannot be resolved with current document set.
   - Maps to decision `request_evidence`.
5. **`escalated`**:
   - Material reporting violation or fraud indicator requiring legal review.
   - Maps to decision `reject` with compliance escalation flag.
