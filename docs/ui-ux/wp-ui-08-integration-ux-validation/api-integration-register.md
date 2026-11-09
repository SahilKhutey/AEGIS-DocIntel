# WP-UI-08: API Integration Register

This register catalogues all frontend-to-backend API integration touchpoints across AEGIS-DocIntel, specifying endpoint URLs, HTTP verbs, payload schemas, and response validation contracts.

| Category | Endpoint | Method | Request Payload / Params | Response Schema Contract | Mapped UI View |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Documents** | `/v1/documents` | GET | `query`, `status`, `limit`, `offset` | `DocumentListResponseSchema` | `/documents` |
| **Documents** | `/v1/documents/{id}` | GET | Path `id` | `DocumentResponseSchema` | `/documents/[documentId]` |
| **Documents** | `/v1/documents/upload` | POST | `multipart/form-data` | `DocumentResponseSchema` | `UploadDialog` |
| **Jobs** | `/v1/jobs` | GET | `status`, `resource_id`, `limit` | `JobListResponseSchema` | `/processing`, `/pipelines` |
| **Jobs** | `/v1/jobs/{id}` | GET | Path `id` | `JobResponseSchema` | `/pipelines/[runId]` |
| **Jobs** | `/v1/jobs/{id}/events`| GET | Path `id` | `z.array(JobEventSchema)` | `/pipelines/[runId]` |
| **Jobs** | `/v1/jobs/{id}/retry` | POST | Path `id` | `JobResponseSchema` | `/pipelines/[runId]` |
| **Intelligence** | `/api/v1/ask` | POST | `question`, `document_ids` | `AnswerSchema` | `/ask` |
| **Intelligence** | `/api/v1/intelligence/compare` | POST | `document_ids`, `mode` | `DocumentComparisonSchema` | `/compare` |
| **Governance** | `/api/v1/reviews` | GET | `status`, `assigned_to`, `limit` | `ReviewListSchema` | `/reviews` |
| **Governance** | `/api/v1/reviews/{id}`| GET | Path `id` | `ReviewItemSchema` | `/reviews/[reviewId]` |
| **Governance** | `/api/v1/reviews/{id}/claim` | POST | `expected_version` | `ReviewItemSchema` | `/reviews/[reviewId]` |
| **Governance** | `/api/v1/reviews/{id}/decision` | POST | `decision`, `rationale`, `expected_version` | `DecisionResponseSchema` | `/reviews/[reviewId]` |
| **Governance** | `/api/v1/reviews/{id}/history` | GET | Path `id` | `AuditHistorySchema` | `/reviews/[reviewId]` |
| **Governance** | `/api/v1/reviews/metrics` | GET | None | `GovernanceMetricsSchema` | `/reviews` |
| **Admin** | `/v1/admin/stats` | GET | None | `TenantStatsSchema` | `/analytics`, `/monitoring` |
| **Admin** | `/v1/admin/token-usage` | GET | `time_range` | `TokenUsageResponseSchema` | `/analytics` |
| **Health** | `/health/ready` | GET | None | `HealthReadyResponseSchema` | `/monitoring` |
| **Health** | `/health/live` | GET | None | `HealthLiveResponseSchema` | `/monitoring` |
| **Developer** | `/v1/webhooks/subscriptions` | GET / POST | `url`, `events`, `secret` | Webhook Schemas | `/developer/webhooks` |
