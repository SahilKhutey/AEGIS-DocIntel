import React from "react";
import { MetricCard } from "@/components/advanced/MetricCard";
import type { TenantStats } from "../types";
import { FileText, Layers, Zap, DollarSign, Clock, ShieldCheck } from "lucide-react";

export interface OverviewMetricsProps {
  stats: TenantStats;
  previousStats?: Partial<TenantStats>;
  isLoading?: boolean;
}

export const OverviewMetrics: React.FC<OverviewMetricsProps> = ({
  stats,
  previousStats,
  isLoading = false,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      <MetricCard
        title="Documents"
        value={stats.doc_count}
        previousValue={previousStats?.doc_count}
        format="number"
        icon={<FileText className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="Total ingested documents"
      />
      <MetricCard
        title="Chunks"
        value={stats.chunk_count}
        previousValue={previousStats?.chunk_count}
        format="number"
        icon={<Layers className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="Indexed vector chunks"
      />
      <MetricCard
        title="Tokens Used"
        value={stats.total_tokens_used}
        previousValue={previousStats?.total_tokens_used}
        format="number"
        icon={<Zap className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="Embedding & LLM tokens"
      />
      <MetricCard
        title="Total Cost"
        value={stats.total_cost_usd}
        previousValue={previousStats?.total_cost_usd}
        format="currency"
        decimals={2}
        icon={<DollarSign className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="API spend for period"
      />
      <MetricCard
        title="Cache Hit Rate"
        value={stats.cache_hit_rate}
        previousValue={previousStats?.cache_hit_rate}
        format="percent"
        decimals={1}
        icon={<ShieldCheck className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="Vector cache efficiency"
      />
      <MetricCard
        title="Avg Query Latency"
        value={stats.avg_query_latency_ms}
        previousValue={previousStats?.avg_query_latency_ms}
        format="duration"
        invertedTrend={true}
        icon={<Clock className="w-4 h-4" aria-hidden="true" />}
        isLoading={isLoading}
        subtext="End-to-end retrieval time"
      />
    </div>
  );
};
