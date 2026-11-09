import { z } from "zod";

export const TenantStatsSchema = z.object({
  tenant_id: z.string(),
  doc_count: z.number().int().nonnegative(),
  chunk_count: z.number().int().nonnegative(),
  total_tokens_used: z.number().int().nonnegative(),
  total_cost_usd: z.number().nonnegative(),
  cache_hit_rate: z.number().min(0).max(1),
  avg_query_latency_ms: z.number().nonnegative(),
});

export const TokenUsageResponseSchema = z.object({
  period: z.string(),
  total_in_tokens: z.number().int().nonnegative(),
  total_out_tokens: z.number().int().nonnegative(),
  total_cost_usd: z.number().nonnegative(),
  query_count: z.number().int().nonnegative(),
  cache_hits: z.number().int().nonnegative(),
  avg_latency_ms: z.number().nonnegative(),
});

export type TenantStats = z.infer<typeof TenantStatsSchema>;
export type TokenUsageResponse = z.infer<typeof TokenUsageResponseSchema>;
