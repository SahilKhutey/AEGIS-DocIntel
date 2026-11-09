# WP-UI-08: API Contract Validation

## 1. Principles of Contract Validation

A core failure mode in AI-powered applications is frontend data fabrication or silent tolerance of degraded responses. WP-UI-08 enforces strict contract validation:

1. **Schema Authority**: The backend FastAPI schemas (`src/api/` and `src/core/`) define the single source of truth.
2. **Runtime Verification**: All responses passing through `apiRequest()` are parsed via Zod schemas. If the backend response deviates from the contract, an `ApiError` with code `SCHEMA_VALIDATION_ERROR` is immediately thrown.
3. **No Silent Defaults**: Missing fields do not default silently to fabricated or zeroed numbers; they fail fast or require explicit optional typing.

---

## 2. API Contract Validators Register

The contract definitions reside in `web/src/features/integration/api-contracts/`:

| Contract File | Schemas | Target Backend Endpoints |
| :--- | :--- | :--- |
| `documents.contract.ts` | `DocumentResponseSchema`<br>`DocumentListResponseSchema` | `GET /v1/documents`<br>`GET /v1/documents/{id}` |
| `jobs.contract.ts` | `JobResponseSchema`<br>`JobEventSchema`<br>`JobListResponseSchema` | `GET /v1/jobs`<br>`GET /v1/jobs/{id}`<br>`GET /v1/jobs/{id}/events` |
| `intelligence.contract.ts`| `CitationSchema`<br>`QueryResponseSchema`<br>`StreamChunkSchema` | `POST /v1/query`<br>`POST /api/v1/ask`<br>`POST /v1/stream` |
| `governance.contract.ts` | `ReviewItemResponseSchema`<br>`ReviewQueueResponseSchema`<br>`ReviewDecisionRequestSchema` | `GET /v1/reviews`<br>`GET /v1/reviews/{id}`<br>`POST /v1/reviews/{id}/decision` |
| `admin.contract.ts` | `TenantStatsSchema`<br>`TokenUsageResponseSchema` | `GET /v1/admin/stats`<br>`GET /v1/admin/token-usage` |
| `health.contract.ts` | `HealthLiveResponseSchema`<br>`HealthReadyResponseSchema` | `GET /health/live`<br>`GET /health/ready` |

---

## 3. Real-World Contract Validation Example

```typescript
import { DocumentListResponseSchema } from "@/features/integration/api-contracts";
import { apiRequest } from "@/lib/api";

// Strongly-typed response verified at runtime
const response = await apiRequest("/v1/documents", DocumentListResponseSchema);
console.log(`Fetched ${response.total} valid documents`);
```
