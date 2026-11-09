"use client";

import React, { useState, useEffect } from "react";
import { RefreshCw } from "lucide-react";

export interface FreshnessBadgeProps {
  lastUpdated: string;
  onRefresh: () => void;
  isLoading?: boolean;
}

export const FreshnessBadge: React.FC<FreshnessBadgeProps> = ({
  lastUpdated,
  onRefresh,
  isLoading = false,
}) => {
  const [secondsAgo, setSecondsAgo] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      const diff = Math.max(0, Math.round((Date.now() - new Date(lastUpdated).getTime()) / 1000));
      setSecondsAgo(diff);
    }, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs">
      <span className="flex items-center gap-1.5 font-medium text-slate-700">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" aria-hidden="true" />
        <span>Freshness: {secondsAgo === 0 ? "Just now" : `${secondsAgo}s ago`}</span>
      </span>

      <button
        type="button"
        onClick={onRefresh}
        disabled={isLoading}
        className="text-slate-500 hover:text-slate-900 transition-colors disabled:opacity-50 cursor-pointer"
        aria-label="Refresh telemetry data"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-blue-600" : ""}`} aria-hidden="true" />
      </button>
    </div>
  );
};
