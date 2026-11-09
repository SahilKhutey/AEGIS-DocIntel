import React from "react";
import type { GovernanceMetrics } from "../types";
import { CheckCircle2, AlertTriangle, XCircle, Shield } from "lucide-react";
import { MetricCard } from "@/components/advanced/MetricCard";

export interface GovernanceAnalyticsProps {
  metrics?: GovernanceMetrics;
  previousMetrics?: Partial<GovernanceMetrics>;
}

export const GovernanceAnalytics: React.FC<GovernanceAnalyticsProps> = ({
  metrics,
  previousMetrics,
}) => {
  if (!metrics) {
    return (
      <div className="p-6 bg-white rounded-xl border border-slate-200 text-center text-xs text-slate-500">
        No governance review metrics available for this period.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Reviewed Items"
          value={metrics.total_items}
          previousValue={previousMetrics?.total_items}
          format="number"
          icon={<Shield className="w-4 h-4 text-blue-600" aria-hidden="true" />}
          subtext="Facts evaluated by reviewers"
        />
        <MetricCard
          title="Approval Rate"
          value={metrics.approval_rate}
          previousValue={previousMetrics?.approval_rate}
          format="percent"
          decimals={1}
          icon={<CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />}
          subtext="Facts approved without edit"
        />
        <MetricCard
          title="Correction Rate"
          value={metrics.correction_rate}
          previousValue={previousMetrics?.correction_rate}
          format="percent"
          decimals={1}
          invertedTrend={true}
          icon={<AlertTriangle className="w-4 h-4 text-amber-500" aria-hidden="true" />}
          subtext="Facts amended before approval"
        />
        <MetricCard
          title="Rejection Rate"
          value={metrics.rejection_rate}
          previousValue={previousMetrics?.rejection_rate}
          format="percent"
          decimals={1}
          invertedTrend={true}
          icon={<XCircle className="w-4 h-4 text-rose-500" aria-hidden="true" />}
          subtext="Facts rejected as inaccurate"
        />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
          Review Decision Distribution
        </h4>
        <div className="flex h-4 w-full rounded-full overflow-hidden bg-slate-100">
          <div
            className="bg-emerald-500 transition-all"
            style={{ width: `${metrics.approval_rate}%` }}
            title={`Approved: ${metrics.approval_rate}%`}
          />
          <div
            className="bg-amber-400 transition-all"
            style={{ width: `${metrics.correction_rate}%` }}
            title={`Corrected: ${metrics.correction_rate}%`}
          />
          <div
            className="bg-rose-500 transition-all"
            style={{ width: `${metrics.rejection_rate}%` }}
            title={`Rejected: ${metrics.rejection_rate}%`}
          />
        </div>
        <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            Approved ({metrics.approval_rate}%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
            Corrected ({metrics.correction_rate}%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
            Rejected ({metrics.rejection_rate}%)
          </span>
        </div>
      </div>
    </div>
  );
};
