import React from "react";
import { Info } from "lucide-react";

export interface EmptyMetricStateProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyMetricState: React.FC<EmptyMetricStateProps> = ({
  title = "No metrics available",
  description = "No telemetry or performance data has been recorded for the selected period.",
  action,
  className = "",
}) => {
  return (
    <div
      role="status"
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 ${className}`}
    >
      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 text-slate-400 mb-3">
        <Info className="w-5 h-5" aria-hidden="true" />
      </div>
      <h4 className="text-sm font-semibold text-slate-800 mb-1">{title}</h4>
      <p className="text-xs text-slate-500 max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
