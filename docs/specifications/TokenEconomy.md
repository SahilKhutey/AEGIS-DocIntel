# AEGIS-DocIntel — Token Economy & Cost Model
**Version 1.0.0**

---

## 1. Fundamental Token Math

### Token Approximations
| Unit              | Token Count        |
|-------------------|--------------------|
| 1 word (English)  | ≈ 1.3 tokens       |
| 1 sentence (20w)  | ≈ 26 tokens        |
| 1 paragraph (5s)  | ≈ 130 tokens       |
| 1 page (250w)     | ≈ 325 tokens       |
| 1 page (500w)     | ≈ 650 tokens       |
| 1 MB of text      | ≈ 350,000 tokens   |

### Document Token Estimates
| Document Type     | Pages | Words    | Tokens Approx |
|-------------------|-------|----------|---------------|
| Executive Summary | 5     | 2,500    | 3,250         |
| Research Paper    | 15    | 7,500    | 9,750         |
| Annual Report     | 80    | 40,000   | 52,000        |
| Technical Manual  | 200   | 100,000  | 130,000       |
| Legal Contract    | 50    | 25,000   | 32,500        |
| Blueprint PDF     | 30    | 5,000    | 6,500 + visuals |

---

## 2. Standard Token Budget Per Query

### Full Context (Naive) — NOT what AEGIS does
```
Full 200-page doc: 130,000 tokens input + 1,000 output = 131,000 tokens
Cost @ GPT-4o ($5/1M in): $0.655 per query
```

### RAG Budget (What AEGIS does)
```
┌─────────────────────────────────────────────────────────────┐
│  COMPONENT                        TOKENS    % OF BUDGET     │
├─────────────────────────────────────────────────────────────┤
│  System prompt + instructions      1,200      14.1%         │
│  Tool definitions                    300       3.5%         │
│  User question                       200       2.4%         │
│  Conversation history (compressed)   800       9.4%         │
│  Citation scaffold                   400       4.7%         │
│  Retrieved chunks (8 × 700 avg)    5,600      65.9%         │
├─────────────────────────────────────────────────────────────┤
│  TOTAL INPUT                        8,500     100%          │
│  OUTPUT                             800–1,500              │
│  GRAND TOTAL                        9,300–10,000           │
└─────────────────────────────────────────────────────────────┘
```

**Token reduction: 93.5% (130,000 → 8,500 input tokens)**

---

## 3. Multi-Tier Cost Model

### Tier 1: Self-Hosted vLLM (A100 80GB)

| Metric                    | Value                          |
|---------------------------|--------------------------------|
| GPU cost (cloud)          | $3.50/hr (A100 80GB)           |
| Throughput (LLaMA-3.3-70B)| ~2,000 tokens/sec (4×A100)     |
| Cost per 1M input tokens  | $0.49 (at 100% utilization)    |
| Cost per 1M output tokens | $0.49                          |
| Cost per RAG query (10K)  | $0.0049                        |
| Cost per query (no cache) | **~$0.005**                    |
| Cost per query (50% cache)| **~$0.0025**                   |

### Tier 2: OpenAI GPT-4o (Managed)

| Scenario                  | Input (5/1M) | Output (15/1M) | Per Query  |
|---------------------------|--------------|----------------|------------|
| Full PDF (130K)           | $0.65        | $0.015         | **$0.665** |
| RAG only (8.5K)           | $0.0425      | $0.015         | **$0.058** |
| RAG + prefix cache (50%)  | $0.021       | $0.015         | **$0.036** |
| RAG + semantic cache (hit)| $0.000       | $0.000         | **$0.000** |

### Tier 3: Anthropic Claude 3.5 Sonnet (Managed)

| Scenario                  | Input (3/1M) | Output (15/1M) | Per Query  |
|---------------------------|--------------|----------------|------------|
| Full PDF (130K)           | $0.39        | $0.015         | **$0.405** |
| RAG only (8.5K)           | $0.0255      | $0.015         | **$0.041** |
| RAG + cache (50% hit)     | $0.013       | $0.015         | **$0.028** |

### Tier 4: Google Gemini 1.5 Pro (Managed)

| Scenario                  | Input (3.5/1M) | Output (10.5/1M) | Per Query  |
|---------------------------|----------------|------------------|------------|
| Full PDF (130K)           | $0.455         | $0.011           | **$0.466** |
| RAG only (8.5K)           | $0.030         | $0.011           | **$0.041** |
| RAG + context cache       | $0.001         | $0.011           | **$0.012** |
| (Context cache: $1.00/1M/hr TTL, 90% cost reduction on cached portion) |

---

## 4. Savings Analysis

### Cost Comparison Table
| Method                            | Cost/Query | Savings vs Naive |
|-----------------------------------|------------|------------------|
| Full PDF → GPT-4o (naive)         | $0.665     | 0% (baseline)    |
| RAG → GPT-4o (no cache)           | $0.058     | 91.3%            |
| RAG → GPT-4o (prefix cache 50%)   | $0.036     | 94.6%            |
| RAG → GPT-4o (semantic cache hit) | $0.000     | 100%             |
| RAG → vLLM/LLaMA (self-hosted)    | $0.005     | 99.2%            |

### Monthly Cost Projection (1M queries/month)

| Configuration                     | Monthly Cost |
|-----------------------------------|--------------|
| Naive GPT-4o (full PDF)           | $665,000     |
| RAG + GPT-4o                      | $58,000      |
| RAG + GPT-4o + all caches         | $14,000      |
| RAG + vLLM (self-hosted, A100×8)  | $5,040       |
| RAG + vLLM + all caches           | $2,520       |

**Self-hosted RAG saves 99.6% vs naive managed full-context**

---

## 5. Caching Economics

### Semantic Cache Analysis
```
Assumption: 1M queries/month, semantic cache hit rate = 40%

Queries hitting cache:    400,000  → $0.00 LLM cost
Queries missing cache:    600,000  → standard RAG cost

Cache infrastructure cost: Redis 32GB @ $200/month
Net savings (GPT-4o RAG): 400,000 × $0.058 = $23,200/month
Cache ROI: 116× return on investment
```

### Context Cache Analysis (Gemini-style)
```
For users who send the same document repeatedly (enterprise use case):

Without context cache: $0.041 × N queries
With context cache:    $0.001 × N queries + $1.00/hr TTL cost

Break-even: ~26 queries per document per hour
Enterprise typical: 100+ queries/hour → 97.6% savings
```

### KV Cache (Prefix Caching)
```
System prompt is identical for all queries:
  1,200 tokens × 100% identical → KV cache hit
  Cost reduction: 14% on input tokens, no latency impact

Implementation: vLLM prefix_caching=True (built-in)
                OpenAI: automatic (no config needed)
```

---

## 6. Token Ledger Implementation

### Database Schema
```sql
-- Per-query token tracking
CREATE TABLE token_usage (
    id           BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    session_id   UUID,
    doc_id       UUID,
    model        TEXT NOT NULL,
    in_tokens    INT NOT NULL,
    out_tokens   INT NOT NULL,
    cache_tokens INT NOT NULL DEFAULT 0,   -- tokens served from cache
    cost_usd     NUMERIC(12, 8),
    latency_ms   INT,
    cache_hit    BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT now()
)
PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE token_usage_2026_06 PARTITION OF token_usage
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

-- Tenant cost summary view
CREATE MATERIALIZED VIEW tenant_cost_summary AS
SELECT
    tenant_id,
    DATE_TRUNC('day', created_at)     AS day,
    SUM(in_tokens)                    AS total_in,
    SUM(out_tokens)                   AS total_out,
    SUM(cost_usd)                     AS total_cost_usd,
    COUNT(*) FILTER (WHERE cache_hit) AS cache_hits,
    COUNT(*)                          AS total_queries,
    AVG(latency_ms)                   AS avg_latency_ms
FROM token_usage
GROUP BY tenant_id, DATE_TRUNC('day', created_at)
WITH DATA;
```

### Token Budget Enforcer (Python)
```python
class TokenBudgetEnforcer:
    """
    Enforces per-tenant token budgets.
    Raises TokenBudgetExceededError if limit hit.
    """

    BUDGET_KEY = "token:budget:{tenant_id}:{period}"

    def __init__(self, redis_client, postgres_pool):
        self.redis = redis_client
        self.pg = postgres_pool

    async def check_and_consume(
        self,
        tenant_id: str,
        in_tokens: int,
        out_tokens: int,
        model: str,
    ) -> dict:
        """Check budget, consume tokens, log usage. Returns cost breakdown."""
        period = datetime.utcnow().strftime("%Y-%m")
        key = self.BUDGET_KEY.format(tenant_id=tenant_id, period=period)

        # Atomic increment with Redis INCRBY
        total_tokens = in_tokens + out_tokens
        new_total = await self.redis.incrby(key, total_tokens)
        await self.redis.expire(key, 86400 * 32)  # 32d TTL

        # Fetch tenant budget limit
        limit = await self._get_limit(tenant_id)
        if new_total > limit:
            raise TokenBudgetExceededError(
                f"Tenant {tenant_id} exceeded monthly token budget: "
                f"{new_total}/{limit}"
            )

        # Calculate cost
        pricing = PRICING_TABLE.get(model, DEFAULT_PRICING)
        cost = (in_tokens * pricing.input_per_token +
                out_tokens * pricing.output_per_token)

        # Async log to Postgres
        asyncio.create_task(
            self._log_usage(tenant_id, in_tokens, out_tokens, model, cost)
        )

        return {"tokens_used": total_tokens, "cost_usd": cost, "budget_remaining": limit - new_total}

    async def _get_limit(self, tenant_id: str) -> int:
        async with self.pg.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT monthly_token_limit FROM tenants WHERE tenant_id = $1",
                tenant_id
            )
            return row["monthly_token_limit"] if row else 10_000_000  # default 10M

    async def _log_usage(self, *args):
        async with self.pg.acquire() as conn:
            await conn.execute(
                """INSERT INTO token_usage (tenant_id, in_tokens, out_tokens, model, cost_usd)
                   VALUES ($1, $2, $3, $4, $5)""",
                *args
            )
```

---

## 7. Adaptive Token Strategy

### Dynamic K Selection
```python
def compute_optimal_k(
    confidence_scores: list[float],
    token_budget: int,
    avg_chunk_tokens: int = 700,
) -> int:
    """
    Dynamically adjust number of retrieved chunks (K)
    based on confidence scores and available token budget.
    """
    max_k = token_budget // avg_chunk_tokens  # absolute max

    if not confidence_scores:
        return min(8, max_k)

    top_score = max(confidence_scores)
    if top_score >= 0.85:
        return min(5, max_k)   # High confidence → fewer chunks needed
    elif top_score >= 0.6:
        return min(10, max_k)  # Medium → standard
    elif top_score >= 0.4:
        return min(15, max_k)  # Low → expand retrieval
    else:
        return min(20, max_k)  # Very low → max retrieval + web search fallback
```

### Prompt Compression (LLMLingua-2)
```
Original chunks: 12,000 tokens
After LLMLingua-2 (ratio=0.5): 6,000 tokens
Quality impact: < 2% on RAG benchmarks
Speed impact: +50ms (negligible vs LLM time)
Cost impact: -30% on LLM input cost
```

---

## 8. Cost Optimization Checklist

| Optimization                      | Implementation         | Savings  |
|-----------------------------------|------------------------|----------|
| ✅ RAG vs full-context            | FAISS/Milvus retrieval | 91–99%   |
| ✅ Semantic caching               | Redis + vector lookup  | 30–50%   |
| ✅ Prefix/KV caching              | vLLM prefix cache      | 14%      |
| ✅ Context caching                | Redis document cache   | 40–90%   |
| ✅ Prompt compression             | LLMLingua-2            | 20–30%   |
| ✅ Dynamic K                      | Confidence-based       | 10–20%   |
| ✅ Model routing                  | Small→large escalation | 30–60%   |
| ✅ Quantization (AWQ 4-bit)       | vLLM AWQ               | 60% GPU  |
| ✅ Chunk deduplication            | MinHash LSH            | 5–15%    |
| ✅ Batching                       | Async query grouping   | 20–40%   |
