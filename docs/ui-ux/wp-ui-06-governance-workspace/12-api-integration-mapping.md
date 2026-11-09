# 12 — API Integration Mapping

## 1. Verified FastAPI Backend Endpoints

Every frontend capability in WP-UI-06 maps directly to verified backend contracts in `contracts/openapi.yaml` and `src/engines/governance/`:

| UI Action | HTTP Method | Endpoint | Request Body | Headers | Response Schema |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Load Queue | `GET` | `/api/v1/reviews` | None (`status`, `limit`, `cursor` query params) | None | `ReviewListSchema` (`items`, `next_cursor`) |
| Load Queue Metrics | `GET` | `/api/v1/reviews/metrics` | None | None | `GovernanceMetricsSchema` |
| Load Review Item | `GET` | `/api/v1/reviews/{id}` | None | None | `ReviewItemSchema` |
| Claim Item | `POST` | `/api/v1/reviews/{id}/claim` | `{ expected_version: number }` | None | `ReviewItemSchema` |
| Submit Decision | `POST` | `/api/v1/reviews/{id}/decisions` | `{ action, expected_version, rationale, corrected_value?, ... }` | `Idempotency-Key` | `DecisionResponseSchema` (`item`, `decision`, `audit_event`) |
| Reopen Item | `POST` | `/api/v1/reviews/{id}/reopen` | `{ expected_version, rationale }` | None | `{ item: ReviewItem }` |
| Load Audit History | `GET` | `/api/v1/reviews/{id}/history` | None | None | `z.array(AuditEventSchema)` |
| Submit Feedback | `POST` | `/api/v1/reviews/{id}/feedback` | `{ category, notes }` | None | `{ status: string }` |

---

## 2. Zero-Fabricated Contract Policy

No phantom or invented endpoints are called. Fact verification outcomes and conflict resolutions are translated directly into formal `/decisions` payloads:
- `verified` -> `approve`
- `partially_verified` -> `correct`
- `not_verified` / `contradicted` -> `reject`
- `insufficient_evidence` -> `request_evidence`
- `accepted_first_fact` -> `approve`
- `accepted_second_fact` -> `correct`
- `both_valid` -> `correct` (reconciled value)
- `escalated` -> `reject`
