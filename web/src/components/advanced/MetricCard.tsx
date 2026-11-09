import React from "react";
import {
  formatMetricValue,
  calculatePercentageChange,
  type MetricFormat,
} from "@/lib/advanced/format-metric";
import { MetricTrend } from "./MetricTrend";

export interface MetricCardProps {
  title: string;
  value: number | null | undefined;
  previousValue?: number | null | undefined;
  format?: MetricFormat;
  decimals?: number;
  subtext?: string;
  icon?: React.ReactNode;
  invertedTrend?: boolean;
  badge?: string;
  isLoading?: boolean;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  previousValue,
  format = "number",
  decimals,
  subtext,
  icon,
  invertedTrend = false,
  badge,
  isLoading = false,
  className = "",
}) => {
  const isAvailable = value !== null && value !== undefined && !Number.isNaN(value);
  const formattedValue = formatMetricValue(value, format, { decimals });
  const change = calculatePercentageChange(value, previousValue);

  return (
    <div
      role="region"
      aria-label={`${title} metric`}
      className={`bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between transition-shadow hover:shadow-sm ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          {icon && <div className="text-slate-500">{icon}</div>}
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {title}
          </h3>
        </div>
        {badge && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium">
            {badge}
          </span>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        {isLoading ? (
          <div className="h-8 w-24 bg-slate-200 rounded animate-pulse" aria-hidden="true" />
        ) : (
          <div
            className={`text-2xl font-bold tracking-tight ${
              isAvailable ? "text-slate-900" : "text-slate-400 italic font-normal"
            }`}
          >
            {formattedValue}
          </div>
        )}

        {!isLoading && change && (
          <MetricTrend change={change} inverted={invertedTrend} />
        )}
      </div>

      {subtext && (
        <p className="mt-2 text-xs text-slate-500 truncate" title={subtext}>
          {subtext}
        </p>
      )}
    </div>
  );
};
