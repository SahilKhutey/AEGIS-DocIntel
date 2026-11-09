# AEGIS-DocIntel — User Workflow Architecture

## 1. Workflow State Machine Architecture

Every core workflow in AEGIS is defined as a deterministic sequence of state transitions with explicit loading, success, error, unauthorized, and retry states.

---

### Workflow A: Document Ingestion

```
[Select File]
    │
    ▼
[Validate File (Client MIME & Size)]
    │
    ├── (Invalid) ──► [Show Error Banner & Allow Reselect]
    │
    ▼
[Submit to API (POST /v1/documents/upload)]
    │
    ▼
[Receive 202 Accepted & Job/Doc ID]
    │
    ▼
[Show Processing Pipeline Progress (SSE / Polling)]
    │
    ├── (Stage Failure) ──► [Show Actionable Error & Retry Action]
    │
    ▼
[Processing Complete (Status: ready)]
    │
    ▼
[Open Document Inspection Studio]
```

**State Specifications:**
- **Loading State**: Upload progress bar with byte counter; stage-by-stage pipeline indicator.
- **Empty State**: Drag-and-drop target zone with supported format icons and size limits.
- **Error State**: Actionable error card displaying backend `X-Request-ID`, error code, and `Retry Upload` button.
- **Success State**: Green confirmation toast with direct navigation button to the inspected document.

---

### Workflow B: Intelligence Query ("Ask AEGIS")

```
[Choose Authorized Source Scope]
    │
    ▼
[Enter Natural Language Question]
    │
    ▼
[Submit Query (POST /v1/answers)]
    │
    ▼
[Stream Answer Tokens (SSE)]
    │
    ▼
[Display Verified Citations [1], [2]]
    │
    ├── (Low Confidence) ──► [Display Insufficient Evidence Warning]
    │
    ▼
[User Clicks Citation Pill]
    │
    ▼
[Open Contextual Evidence Inspector (Synchronized PDF Canvas & Bounding Box)]
```

**State Specifications:**
- **Loading State**: Pulsing skeleton text stream with token counter; decomposition accordion.
- **Empty State**: Helpful prompt suggestions and authorized document scope selector.
- **Error State**: Query error banner with retry option and network status indicator.
- **Insufficient Evidence**: Explicit warning state preventing speculative generation.

---

### Workflow C: Governance Review

```
[Open Review Queue (/reviews)]
    │
    ▼
[Filter by Priority, Status, or Conflict Type]
    │
    ▼
[Claim Review Item (POST /v1/reviews/{id}/claim)]
    │
    ▼
[Inspect Candidate Fact & Source Evidence Canvas]
    │
    ▼
[Select Sovereign Decision (Approve / Correct / Reject / Request Evidence)]
    │
    ▼
[Enter Mandatory Rationale & Correction Fields]
    │
    ▼
[Submit Decision (POST /v1/reviews/{id}/decisions)]
    │
    ▼
[Confirm Server Response & Append Immutable Audit Event]
    │
    ▼
[Auto-advance to Next Prioritized Queue Item]
```

**State Specifications:**
- **Loading State**: Shimmering card skeleton for review details and evidence quotes.
- **Empty State**: "Review Queue Clear" illustration with celebration indicator.
- **Concurrency Conflict**: Warning banner if another reviewer claimed the item in another session.
- **Success State**: Audit event recorded with version increment badge (`v1` $\to$ `v2`).

---

### Workflow D: Document Comparison

```
[Select Document A] ──► [Select Document B]
    │
    ▼
[Validate Compatibility & Permissions]
    │
    ▼
[Request Comparison (POST /v1/intelligence/compare)]
    │
    ▼
[Render Assertion Matrix (Matches vs Conflicts)]
    │
    ▼
[Inspect Supporting Evidence Quotes]
    │
    ├── (Contradiction Found) ──► [One-Click Escalate to Review Queue]
    │
    ▼
[Export Comparison Summary Package]
```

**State Specifications:**
- **Loading State**: Matrix computation spinner with document comparison progress bar.
- **Empty State**: Document pair selector with recent comparisons history.
- **Conflict Highlighting**: Red-tinted assertion rows with side-by-side evidence diffs.
