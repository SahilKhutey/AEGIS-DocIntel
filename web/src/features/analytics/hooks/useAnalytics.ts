"use client";

import { useState, useEffect, useCallback } from "react";
import type { TimeRangePreset } from "@/lib/advanced/time-range";
import type { AnalyticsSnapshot } from "../types";
import { getAnalyticsSnapshot } from "../api/analytics.api";
import { toCsv, downloadCsv } from "@/lib/advanced/export-data";

export function useAnalytics(initialRange: TimeRangePreset = "7d") {
  const [timeRange, setTimeRange] = useState<TimeRangePreset>(initialRange);
  const [data, setData] = useState<AnalyticsSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (range: TimeRangePreset) => {
    setIsLoading(true);
    setError(null);
    try {
      const snapshot = await getAnalyticsSnapshot(range);
      setData(snapshot);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(timeRange);
  }, [timeRange, loadData]);

  const handleExportCsv = useCallback(() => {
    if (!data) return;

    const rows = [
      {
        Metric: "Total Documents",
        Category: "Storage & Ingestion",
        Value: data.stats.doc_count,
        Unit: "count",
      },
      {
        Metric: "Total Chunks",
        Category: "Storage & Ingestion",
        Value: data.stats.chunk_count,
        Unit: "count",
      },
      {
        Metric: "Total Tokens Used",
        Category: "Intelligence",
        Value: data.stats.total_tokens_used,
        Unit: "tokens",
      },
      {
        Metric: "Total Estimated Cost",
        Category: "Intelligence",
        Value: data.stats.total_cost_usd,
        Unit: "USD",
      },
      {
        Metric: "Cache Hit Rate",
        Category: "Performance",
        Value: `${data.stats.cache_hit_rate}%`,
        Unit: "percent",
      },
      {
        Metric: "Average Query Latency",
        Category: "Performance",
        Value: `${data.stats.avg_query_latency_ms}ms`,
        Unit: "milliseconds",
      },
    ];

    if (data.governanceMetrics) {
      rows.push(
        {
          Metric: "Total Governance Reviews",
          Category: "Governance",
          Value: data.governanceMetrics.total_items,
          Unit: "count",
        },
        {
          Metric: "Review Approval Rate",
          Category: "Governance",
          Value: `${data.governanceMetrics.approval_rate}%`,
          Unit: "percent",
        },
        {
          Metric: "Review Correction Rate",
          Category: "Governance",
          Value: `${data.governanceMetrics.correction_rate}%`,
          Unit: "percent",
        },
        {
          Metric: "Review Rejection Rate",
          Category: "Governance",
          Value: `${data.governanceMetrics.rejection_rate}%`,
          Unit: "percent",
        },
      );
    }

    const csvContent = toCsv(rows, [
      { key: "Metric", label: "Metric Name" },
      { key: "Category", label: "Category" },
      { key: "Value", label: "Recorded Value" },
      { key: "Unit", label: "Unit of Measure" },
    ]);

    downloadCsv(`aegis-analytics-${timeRange}-${new Date().toISOString().slice(0, 10)}.csv`, csvContent);
  }, [data, timeRange]);

  return {
    timeRange,
    setTimeRange,
    data,
    isLoading,
    error,
    refresh: () => loadData(timeRange),
    exportCsv: handleExportCsv,
  };
}
