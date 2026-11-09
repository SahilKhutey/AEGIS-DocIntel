# 07 — State Machine and Transitions

## 1. Governance State Machine Architecture

The review lifecycle implements a strict finite state machine directly mirroring backend policies in `src/engines/governance/policy.py`.

### States
- `pending`: Newly extracted candidate awaiting human reviewer claim.
- `in_review`: Claimed by an active reviewer; decisions can be evaluated.
- `approved`: Terminal state indicating verified truth.
- `corrected`: Terminal state indicating human-corrected truth with revision history.
- `rejected`: Terminal state indicating discarded or refuted inference.
- `needs_evidence`: Non-terminal state indicating missing context or re-extraction requirement.

---

## 2. Transition Matrix

| Initial State | Allowed Actions | Target State | Actor Requirements | Substantive Payload |
| :--- | :--- | :--- | :--- | :--- |
| `pending` | `claim` | `in_review` | Reviewer / Admin | `expected_version` |
| `needs_evidence` | `claim` | `in_review` | Reviewer / Admin | `expected_version` |
| `in_review` | `approve` | `approved` | Assigned Reviewer / Admin | `expected_version`, `rationale` (min 3 chars) |
| `in_review` | `correct` | `corrected` | Assigned Reviewer / Admin | `expected_version`, `rationale`, `corrected_value`, `evidence_quote` |
| `in_review` | `reject` | `rejected` | Assigned Reviewer / Admin | `expected_version`, `rationale` (min 3 chars) |
| `in_review` | `request_evidence`| `needs_evidence` | Assigned Reviewer / Admin | `expected_version`, `rationale` (min 3 chars) |
| `approved` | `reopen` | `in_review` | Administrator only | `expected_version`, `rationale` (min 5 chars) |
| `corrected` | `reopen` | `in_review` | Administrator only | `expected_version`, `rationale` (min 5 chars) |
| `rejected` | `reopen` | `in_review` | Administrator only | `expected_version`, `rationale` (min 5 chars) |

---

## 3. Terminal Locking & Administrative Reopen

Terminal states (`approved`, `corrected`, `rejected`) lock the candidate from standard modifications.
Only users with administrator privileges can trigger an administrative reopen. Reopening requires:
1. Substantive administrative justification (min 5 characters).
2. Explicit `expected_version` check.
3. Generation of a sequenced audit event documenting the reopen justification.
