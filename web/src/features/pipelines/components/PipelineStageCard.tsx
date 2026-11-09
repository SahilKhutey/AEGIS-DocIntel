import React from "react";
import type { PipelineStage } from "../types";
import { Cpu, Clock, AlertTriangle, Layers, GitCommit } from "lucide-react";

export interface PipelineStageCardProps {
  stage: PipelineStage;
}

export const PipelineStageCard: React.FC<PipelineStageCardProps> = ({ stage }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <h3 className="text-sm font-bold text-slate-900">{stage.name}</h3>
        </div>
        <span
          className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
            stage.status === "succeeded"
              ? "bg-emerald-50 text-emerald-700"
              : stage.status === "running"
              ? "bg-blue-50 text-blue-700"
              : stage.status === "failed"
              ? "bg-rose-50 text-rose-700"
              : "bg-slate-100 text-slate-600"
          }`}
        >
          {stage.status}
        </span>
      </div>

      <dl className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-400 font-medium mb-1 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Duration</span>
          </dt>
          <dd className="font-mono font-bold text-slate-800">
            {stage.durationMs ? `${stage.durationMs}ms` : "Pending execution"}
          </dd>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-400 font-medium mb-1 flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Worker Instance</span>
          </dt>
          <dd className="font-mono font-bold text-slate-800">
            {stage.workerId || "Unassigned"}
          </dd>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-400 font-medium mb-1 flex items-center gap-1">
            <GitCommit className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Dependencies</span>
          </dt>
          <dd className="font-mono font-semibold text-slate-800">
            {stage.dependsOn.length > 0 ? stage.dependsOn.join(", ") : "None (Root)"}
          </dd>
        </div>
      </dl>

      {/* Error Details if Failed */}
      {stage.error && (
        <div role="alert" className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-900 space-y-2">
          <div className="flex items-center gap-2 font-bold text-rose-800">
            <AlertTriangle className="w-4 h-4 text-rose-600" aria-hidden="true" />
            <span>Failure Error Code: {stage.error.code}</span>
          </div>
          <p className="font-mono text-slate-700 bg-white/70 p-2.5 rounded border border-rose-200">
            {stage.error.message}
          </p>
          {stage.error.details && (
            <p className="text-[11px] text-rose-700">{stage.error.details}</p>
          )}
        </div>
      )}
    </div>
  );
};
