import React from "react";
import type { GovernanceMetrics } from "../types";

interface GovernanceMetricsBannerProps {
  metrics: GovernanceMetrics | null;
}

export function GovernanceMetricsBanner({ metrics }: GovernanceMetricsBannerProps) {
  if (!metrics) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" data-testid="governance-metrics">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Total Queue
        </span>
        <p className="mt-1 text-2xl font-bold text-gray-900">{metrics.total_items}</p>
      </div>
      <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 shadow-xs">
        <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
          Approval Rate
        </span>
        <p className="mt-1 text-2xl font-bold text-emerald-800">
          {(metrics.approval_rate * 100).toFixed(0)}%
        </p>
      </div>
      <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4 shadow-xs">
        <span className="text-xs font-semibold uppercase tracking-wider text-purple-700">
          Correction Rate
        </span>
        <p className="mt-1 text-2xl font-bold text-purple-800">
          {(metrics.correction_rate * 100).toFixed(0)}%
        </p>
      </div>
      <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-4 shadow-xs">
        <span className="text-xs font-semibold uppercase tracking-wider text-rose-700">
          Rejection Rate
        </span>
        <p className="mt-1 text-2xl font-bold text-rose-800">
          {(metrics.rejection_rate * 100).toFixed(0)}%
        </p>
      </div>
    </div>
  );
}
