import { z } from "zod";

export const TenantStatsSchema = z.object({
  doc_count: z.number().nonnegative(),
  chunk_count: z.number().nonnegative(),
  total_tokens_used: z.number().nonnegative(),
  total_cost_usd: z.number().nonnegative(),
  cache_hit_rate: z.number().min(0).max(100),
  avg_query_latency_ms: z.number().nonnegative(),
});

export const TokenUsageSchema = z.object({
  total_tokens: z.number().nonnegative(),
  prompt_tokens: z.number().nonnegative(),
  completion_tokens: z.number().nonnegative(),
  estimated_cost_usd: z.number().nonnegative(),
  model_breakdowns: z.record(z.string(), z.number()).optional(),
});

export const GovernanceMetricsSchema = z.object({
  total_items: z.number().nonnegative(),
  approval_rate: z.number().min(0).max(100),
  correction_rate: z.number().min(0).max(100),
  rejection_rate: z.number().min(0).max(100),
});
