"use client";

import React from "react";
import { CheckCircle2, Clock, AlertTriangle, Loader2 } from "lucide-react";
import type { ProcessingStage } from "../types";

export type ProcessingTimelineProps = {
  stages: ProcessingStage[];
  className?: string;
};

export function ProcessingTimeline({ stages, className = "" }: ProcessingTimelineProps) {
  const totalDuration = stages.reduce(
    (acc, stage) => acc + (stage.durationSeconds || 0),
    0
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {totalDuration > 0 && (
        <div className="flex items-center gap-1.5 text-xs text-[var(--muted)]">
          <Clock className="h-3.5 w-3.5" />
          <span>Total execution time: {totalDuration.toFixed(1)}s</span>
        </div>
      )}

      <ol
        className="relative border-l border-[var(--border)] ml-3 space-y-6"
        aria-label="Processing stages"
      >
        {stages.map((stage, idx) => {
          const isCompleted = stage.status === "completed";
          const isRunning = stage.status === "running";
          const isFailed = stage.status === "failed";

          return (
            <li
              key={stage.id || idx}
              className="ml-6 group"
              {...(isRunning ? { "aria-current": "step" as const } : {})}
            >
              <span
                className={[
                  "absolute -left-3 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-[var(--surface)] text-xs font-medium",
                  isCompleted
                    ? "bg-emerald-600 text-white"
                    : isRunning
                      ? "bg-blue-600 text-white animate-pulse"
                      : isFailed
                        ? "bg-red-600 text-white"
                        : "bg-[var(--surface-muted)] text-[var(--muted)] border border-[var(--border)]",
                ].join(" ")}
              >
                {isCompleted ? (
                  <CheckCircle2 className="h-3.5 w-3.5" />
                ) : isRunning ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : isFailed ? (
                  <AlertTriangle className="h-3.5 w-3.5" />
                ) : (
                  <span>{idx + 1}</span>
                )}
              </span>

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                <h4
                  className={[
                    "text-sm font-semibold tracking-tight",
                    isRunning
                      ? "text-blue-600 dark:text-blue-400 font-bold"
                      : isFailed
                        ? "text-red-600 dark:text-red-400 font-bold"
                        : "text-[var(--foreground)]",
                  ].join(" ")}
                >
                  {stage.name}
                </h4>

                <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
                  {stage.durationSeconds != null && (
                    <span className="tabular-nums font-mono">{stage.durationSeconds.toFixed(1)}s</span>
                  )}
                  <span
                    className={[
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                      isCompleted
                        ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                        : isRunning
                          ? "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
                          : isFailed
                            ? "bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300"
                            : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
                    ].join(" ")}
                  >
                    {stage.status}
                  </span>
                </div>
              </div>

              {stage.errorMessage && (
                <div
                  role="alert"
                  className="mt-2 rounded-md bg-red-50 dark:bg-red-950/30 p-2.5 text-xs text-red-800 dark:text-red-300 border border-red-200 dark:border-red-900/50"
                >
                  {stage.errorMessage}
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
