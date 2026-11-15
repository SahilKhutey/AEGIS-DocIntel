import React from "react";
import type { LatencyPercentileData } from "../types";
import { Clock, CheckCircle2 } from "lucide-react";

export interface LatencyPercentilesProps {
  percentiles: LatencyPercentileData;
}

export const LatencyPercentiles: React.FC<LatencyPercentilesProps> = ({ percentiles }) => {
  const maxScale = Math.max(500, percentiles.p99 * 1.2);

  const items = [
    { label: "P50 (Median)", val: percentiles.p50, desc: "50% of requests faster than" },
    { label: "P90", val: percentiles.p90, desc: "90% of requests faster than" },
    { label: "P95 (SLA Threshold)", val: percentiles.p95, desc: "95% of requests faster than" },
    { label: "P99 (Tail Latency)", val: percentiles.p99, desc: "Tail 1% outlier requests" },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">Request & Query Latency Distribution</h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200 font-medium">
          <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
          <span>P95 within SLA (&lt; {percentiles.targetP95}ms)</span>
        </div>
      </div>

      <div className="space-y-4">
        {items.map((item) => {
          const barPct = Math.min(100, (item.val / maxScale) * 100);
          return (
            <div key={item.label} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-800">{item.label}</span>
                <span className="font-mono font-bold text-slate-900">{item.val}ms</span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div
                  className={`h-2.5 rounded-full transition-all ${
                    item.val > percentiles.targetP95 ? "bg-amber-500" : "bg-blue-600"
                  }`}
                  style={{ width: `${barPct}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-600 block">{item.desc}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
