import React from "react";
import {
  TIME_RANGE_OPTIONS,
  type TimeRangePreset,
} from "@/lib/advanced/time-range";
import { Calendar } from "lucide-react";

export interface TimeRangeSelectorProps {
  value: TimeRangePreset;
  onChange: (preset: TimeRangePreset) => void;
  className?: string;
  disabled?: boolean;
}

export const TimeRangeSelector: React.FC<TimeRangeSelectorProps> = ({
  value,
  onChange,
  className = "",
  disabled = false,
}) => {
  return (
    <div
      role="group"
      aria-label="Select analytics time range"
      className={`inline-flex items-center gap-1.5 rounded-lg bg-slate-100 p-1 border border-slate-200 ${className}`}
    >
      <div className="flex items-center px-2 py-1 text-slate-400">
        <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
      </div>
      {TIME_RANGE_OPTIONS.map((opt) => {
        const isSelected = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            disabled={disabled}
            aria-pressed={isSelected}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1.5 h-8 min-h-[32px] box-border text-xs font-medium rounded-md transition-all ${
              isSelected
                ? "bg-white text-slate-900 shadow-xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
            } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
};
