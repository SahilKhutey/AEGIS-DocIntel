# 03 — Fact Verification Specification

## 1. Overview and Route

- **Primary Route**: `/reviews/[reviewId]` (Tab: "Fact Verification")
- **Deep-Link Route**: `/reviews/[reviewId]/verification`
- **Component**: `web/src/features/governance/components/FactVerificationPanel.tsx`

Fact verification provides a comparative workbench where an authorized reviewer verifies a single extracted candidate fact against cited source text passages.

---

## 2. Information Architecture

```
+-----------------------------------------------------------------------------------+
| Fact Verification: Acme Corporation • revenue_q3_2026      Confidence: 98% (High) |
+--------------------------------------------------+--------------------------------+
| EXTRACTED STATEMENT & METADATA                   | CITED EVIDENCE PASSAGE         |
| Subject: Acme Corporation                        | [Grounded Citation]            |
| Attribute: revenue_q3_2026                       | "Acme Corporation reported Q3  |
| Inferred Value: $142.5M                          |  2026 revenue of $142.5M."     |
| Raw Text: "revenue of $142.5 million"            |                                |
| Document: doc-alpha-001  Page: 1                 | Authoritative Source Excerpt:  |
| [Open Document ->]                               | [ Textarea: Verifying quote ]  |
+--------------------------------------------------+--------------------------------+
| VERIFICATION OUTCOMES:                                                            |
| [ Fully Verified ] [ Partially Verified ] [ Not Verified ] [ Contradicted ]      |
| [ Insufficient Evidence ]                                                         |
|                                                                                   |
| Verification Rationale (required):                                                |
| [ Textarea: Audited reasoning for verification outcome...                       ] |
|                                                                                   |
| [ Recommended Action: APPROVE ]               [ Record Verification & Proceed -> ] |
+-----------------------------------------------------------------------------------+
```

---

## 3. Verification Outcomes & State Mapping

| Outcome | Meaning | Recommended Formal Decision Action |
| :--- | :--- | :--- |
| `verified` | Fully substantiated by source text | `approve` |
| `partially_verified` | Core assertion accurate, but requires human value/unit correction | `correct` |
| `not_verified` | Source text does not substantiate assertion | `reject` |
| `contradicted` | Source text directly refutes the claim | `reject` |
| `insufficient_evidence` | Ambiguous or incomplete text requires additional context | `request_evidence` |

---

## 4. Human-in-the-Loop Safeguards

1. **Mandatory Rationale**: Reviewers must provide at least 3 characters explaining why an outcome was reached.
2. **Value Correction Guard**: When selecting `partially_verified`, a dedicated input field dynamically appears requiring the human-corrected value.
3. **Traceable Passage Binding**: The reviewer can inspect or edit the authoritative excerpt that will be permanently stored in the audit trail.
