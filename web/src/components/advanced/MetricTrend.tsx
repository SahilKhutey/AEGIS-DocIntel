import React from "react";
import { ArrowUpRight, ArrowDownRight, Minus } from "lucide-react";
import type { MetricChange } from "@/lib/advanced/format-metric";

export interface MetricTrendProps {
  change: MetricChange | null;
  inverted?: boolean; // If true, decrease is good (e.g. latency, error rate)
  className?: string;
}

export const MetricTrend: React.FC<MetricTrendProps> = ({
  change,
  inverted = false,
  className = "",
}) => {
  if (!change) return null;

  const { direction, formattedText } = change;

  let isPositive = direction === "increase";
  if (inverted) {
    isPositive = direction === "decrease";
  }

  let colorClass = "text-slate-500 bg-slate-100";
  let Icon = Minus;

  if (direction === "increase") {
    Icon = ArrowUpRight;
    colorClass = isPositive ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50";
  } else if (direction === "decrease") {
    Icon = ArrowDownRight;
    colorClass = isPositive ? "text-emerald-700 bg-emerald-50" : "text-rose-700 bg-rose-50";
  }

  const accessibleLabel = `${direction === "increase" ? "Increased" : direction === "decrease" ? "Decreased" : "Unchanged"} by ${formattedText}`;

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium ${colorClass} ${className}`}
      aria-label={accessibleLabel}
      title={accessibleLabel}
    >
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      <span>{formattedText}</span>
    </span>
  );
};
