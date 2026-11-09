# Backend Gap Register — WP-UI-07 Advanced Interfaces

## 1. Verified Endpoints in Production
The following backend endpoints match the OpenAPI contracts and are directly integrated:

| Endpoint | Method | Backend Router | Verification Status |
| :--- | :--- | :--- | :--- |
| `/v1/admin/stats` | GET | `src/api/routers/admin.py` | Verified against `TenantStats` contract |
| `/v1/admin/token-usage` | GET | `src/api/routers/admin.py` | Verified token breakdown & model breakdowns |
| `/v1/reviews/metrics` | GET | `src/api/routers/reviews.py` | Verified `GovernanceMetrics` |
| `/v1/jobs` | GET | `src/api/routers/jobs.py` | Verified job list filtering and pagination |
| `/v1/jobs/{id}` | GET | `src/api/routers/jobs.py` | Verified single job details |
| `/v1/jobs/{id}/events` | GET | `src/api/routers/jobs.py` | Verified sequential event trail |
| `/v1/jobs/{id}/retry` | POST | `src/api/routers/jobs.py` | Verified authorized retry trigger |
| `/v1/jobs/{id}/cancel` | POST | `src/api/routers/jobs.py` | Verified job cancellation signal |
| `/health/ready` | GET | `src/api/routers/health.py` | Verified dependency health checks |
| `/health/live` | GET | `src/api/routers/health.py` | Verified process liveness |
| `/v1/webhooks/subscriptions` | GET/POST | `src/api/routers/webhooks.py` | Verified SSRF filtering via `is_safe_webhook_url` |
| `/v1/webhooks/subscriptions/{id}` | DELETE | `src/api/routers/webhooks.py` | Verified subscription removal |
| `/v1/advanced/math/unified-evaluation` | POST | `src/api/routers/advanced_features.py` | Verified expression evaluation |
| `/v1/advanced/topology/percolation-check` | GET | `src/api/routers/advanced_features.py` | Verified graph connectivity |

## 2. Recommended Backend Enhancements
1. **Time Range Query Filtering**:
   - `GET /v1/admin/stats` currently returns tenant cumulative stats. A future enhancement should accept query params `?start_time={iso}&end_time={iso}` for time-sliced historical metric comparison.
2. **Streaming Pipeline Stage Updates**:
   - Background jobs currently rely on polling. Adding Server-Sent Events (SSE) via `GET /v1/jobs/{id}/stream` will enable real-time sub-second DAG node transitions without client-side interval polling.
