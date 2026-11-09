# 12 — API Integration Mapping

## 1. Backend Router Alignment
Every UI screen maps directly to verified FastAPI backend routes defined in `src/api/routers/`:

```mermaid
flowchart LR
    subgraph UI ["Frontend Views"]
        V_Analytics["/analytics"]
        V_Math["/mathematics"]
        V_Pipelines["/pipelines"]
        V_Mon["/monitoring"]
        V_Dev["/developer"]
    end

    subgraph API ["FastAPI Backend Endpoints"]
        E_Stats["GET /v1/admin/stats\nGET /v1/admin/token-usage"]
        E_Gov["GET /v1/reviews/metrics"]
        E_AdvMath["POST /v1/advanced/math/unified-evaluation\nGET /v1/advanced/topology/percolation-check"]
        E_Jobs["GET /v1/jobs\nPOST /v1/jobs/{id}/retry\nGET /v1/jobs/{id}/events"]
        E_Health["GET /health/ready\nGET /health/live"]
        E_Webhooks["GET /v1/webhooks/subscriptions\nPOST /v1/webhooks/subscriptions\nDELETE /v1/webhooks/subscriptions/{id}"]
    end

    V_Analytics --> E_Stats
    V_Analytics --> E_Gov
    V_Math --> E_AdvMath
    V_Pipelines --> E_Jobs
    V_Mon --> E_Health
    V_Mon --> E_Stats
    V_Dev --> E_Webhooks
```

## 2. Invariant: Honest Fallbacks
When offline or encountering network partitions, components present explicit error boundaries (`ErrorState`) or deterministic mock fallback contracts rather than crashing the client session.
