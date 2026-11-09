import {
  type TenantStats,
  type TokenUsageData,
  type GovernanceMetrics,
  type AnalyticsSnapshot,
} from "../types";
import {
  TenantStatsSchema,
  TokenUsageSchema,
  GovernanceMetricsSchema,
} from "../schemas/analytics.schema";
import type { TimeRangePreset } from "@/lib/advanced/time-range";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MOCK_STATS_BY_RANGE: Record<TimeRangePreset, TenantStats> = {
  "24h": {
    doc_count: 14,
    chunk_count: 320,
    total_tokens_used: 124500,
    total_cost_usd: 1.86,
    cache_hit_rate: 68.4,
    avg_query_latency_ms: 184,
  },
  "7d": {
    doc_count: 78,
    chunk_count: 1850,
    total_tokens_used: 742000,
    total_cost_usd: 11.13,
    cache_hit_rate: 64.2,
    avg_query_latency_ms: 196,
  },
  "30d": {
    doc_count: 245,
    chunk_count: 6400,
    total_tokens_used: 2840000,
    total_cost_usd: 42.6,
    cache_hit_rate: 61.8,
    avg_query_latency_ms: 210,
  },
  "90d": {
    doc_count: 580,
    chunk_count: 15200,
    total_tokens_used: 7120000,
    total_cost_usd: 106.8,
    cache_hit_rate: 59.4,
    avg_query_latency_ms: 225,
  },
  all: {
    doc_count: 890,
    chunk_count: 24300,
    total_tokens_used: 12400000,
    total_cost_usd: 186.0,
    cache_hit_rate: 62.1,
    avg_query_latency_ms: 205,
  },
  custom: {
    doc_count: 120,
    chunk_count: 3100,
    total_tokens_used: 1450000,
    total_cost_usd: 21.75,
    cache_hit_rate: 65.0,
    avg_query_latency_ms: 190,
  },
};

const MOCK_PREVIOUS_STATS: Partial<TenantStats> = {
  doc_count: 65,
  chunk_count: 1600,
  total_tokens_used: 680000,
  total_cost_usd: 10.2,
  cache_hit_rate: 60.1,
  avg_query_latency_ms: 230,
};

const MOCK_TOKEN_USAGE: TokenUsageData = {
  total_tokens: 742000,
  prompt_tokens: 584000,
  completion_tokens: 158000,
  estimated_cost_usd: 11.13,
  model_breakdowns: {
    "text-embedding-3-small": 310000,
    "gemini-1.5-pro": 280000,
    "gpt-4o-mini": 152000,
  },
};

const MOCK_GOVERNANCE_METRICS: GovernanceMetrics = {
  total_items: 84,
  approval_rate: 82.1,
  correction_rate: 11.9,
  rejection_rate: 6.0,
};

export async function getTenantStats(
  timeRange: TimeRangePreset = "7d",
): Promise<TenantStats> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/admin/stats?range=${timeRange}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return TenantStatsSchema.parse(json);
  } catch {
    return MOCK_STATS_BY_RANGE[timeRange] || MOCK_STATS_BY_RANGE["7d"];
  }
}

export async function getTokenUsage(
  timeRange: TimeRangePreset = "7d",
): Promise<TokenUsageData> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/admin/token-usage?range=${timeRange}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return TokenUsageSchema.parse(json);
  } catch {
    return MOCK_TOKEN_USAGE;
  }
}

export async function getGovernanceMetrics(
  timeRange: TimeRangePreset = "7d",
): Promise<GovernanceMetrics> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/reviews/metrics?range=${timeRange}`, {
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return GovernanceMetricsSchema.parse(json);
  } catch {
    return MOCK_GOVERNANCE_METRICS;
  }
}

export async function getAnalyticsSnapshot(
  timeRange: TimeRangePreset = "7d",
): Promise<AnalyticsSnapshot> {
  const [stats, tokenUsage, governanceMetrics] = await Promise.all([
    getTenantStats(timeRange),
    getTokenUsage(timeRange),
    getGovernanceMetrics(timeRange),
  ]);

  return {
    timeRange,
    updatedAt: new Date().toISOString(),
    stats,
    previousStats: MOCK_PREVIOUS_STATS,
    tokenUsage,
    previousTokenUsage: {
      total_tokens: 680000,
      estimated_cost_usd: 10.2,
    },
    governanceMetrics,
    previousGovernanceMetrics: {
      total_items: 72,
      approval_rate: 79.5,
      correction_rate: 13.5,
      rejection_rate: 7.0,
    },
  };
}
