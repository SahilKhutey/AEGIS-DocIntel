"use client";

import React from "react";
import type { PipelineStage, PipelineStageStatus } from "../types";
import { CheckCircle2, Clock, AlertCircle, PlayCircle, MinusCircle } from "lucide-react";

export interface PipelineGraphProps {
  stages: PipelineStage[];
  selectedStageId?: string | null;
  onSelectStage?: (stageId: string) => void;
}

export const PipelineGraph: React.FC<PipelineGraphProps> = ({
  stages,
  selectedStageId,
  onSelectStage,
}) => {
  const getStatusIcon = (status: PipelineStageStatus) => {
    switch (status) {
      case "succeeded":
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" aria-hidden="true" />;
      case "running":
        return <Clock className="w-4 h-4 text-blue-600 animate-spin" aria-hidden="true" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-rose-600" aria-hidden="true" />;
      case "skipped":
        return <MinusCircle className="w-4 h-4 text-slate-400" aria-hidden="true" />;
      case "idle":
      default:
        return <PlayCircle className="w-4 h-4 text-slate-300" aria-hidden="true" />;
    }
  };

  const getStatusBorder = (status: PipelineStageStatus, isSelected: boolean) => {
    if (isSelected) return "ring-2 ring-blue-600 border-blue-600 bg-blue-50/20";
    switch (status) {
      case "succeeded":
        return "border-emerald-200 bg-white hover:border-emerald-300";
      case "running":
        return "border-blue-300 bg-blue-50/40 animate-pulse";
      case "failed":
        return "border-rose-300 bg-rose-50/30 hover:border-rose-400";
      case "skipped":
        return "border-dashed border-slate-200 bg-slate-50/50 opacity-60";
      case "idle":
      default:
        return "border-slate-200 bg-white hover:border-slate-300";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Execution DAG & Stage Lifecycle</h3>
          <p className="text-xs text-slate-500">
            Directed dependency graph illustrating sequential and branching processing stages.
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            Succeeded
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            Running
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
            Failed
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block" />
            Idle / Skipped
          </span>
        </div>
      </div>

      {/* Visual Pipeline Stage Flow */}
      <div className="overflow-x-auto py-4">
        <div className="flex items-center gap-3 min-w-max">
          {stages.map((stage, idx) => {
            const isSelected = selectedStageId === stage.id;
            const hasNext = idx < stages.length - 1;

            return (
              <React.Fragment key={stage.id}>
                <button
                  type="button"
                  onClick={() => onSelectStage?.(stage.id)}
                  className={`flex flex-col justify-between w-48 p-3 rounded-xl border transition-all text-left cursor-pointer shadow-2xs ${getStatusBorder(
                    stage.status,
                    isSelected,
                  )}`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-mono text-slate-400 font-semibold uppercase">
                      Stage {idx + 1}
                    </span>
                    {getStatusIcon(stage.status)}
                  </div>

                  <h4 className="text-xs font-bold text-slate-800 line-clamp-2 leading-snug mb-2">
                    {stage.name}
                  </h4>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100 font-mono">
                    <span>
                      {stage.durationMs ? `${stage.durationMs}ms` : "—"}
                    </span>
                    <span className="capitalize font-semibold text-slate-600">
                      {stage.status}
                    </span>
                  </div>
                </button>

                {hasNext && (
                  <div className="flex items-center justify-center text-slate-300">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
