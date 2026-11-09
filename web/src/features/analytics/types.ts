import type { TimeRangePreset } from "@/lib/advanced/time-range";

export interface TenantStats {
  doc_count: number;
  chunk_count: number;
  total_tokens_used: number;
  total_cost_usd: number;
  cache_hit_rate: number;
  avg_query_latency_ms: number;
}

export interface TokenUsageData {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number;
  model_breakdowns?: Record<string, number>;
}

export interface GovernanceMetrics {
  total_items: number;
  approval_rate: number;
  correction_rate: number;
  rejection_rate: number;
}

export interface AnalyticsSnapshot {
  timeRange: TimeRangePreset;
  updatedAt: string;
  stats: TenantStats;
  previousStats?: Partial<TenantStats>;
  tokenUsage?: TokenUsageData;
  previousTokenUsage?: Partial<TokenUsageData>;
  governanceMetrics?: GovernanceMetrics;
  previousGovernanceMetrics?: Partial<GovernanceMetrics>;
}

export interface DocumentTypeDistribution {
  type: string;
  count: number;
  percentage: number;
}
