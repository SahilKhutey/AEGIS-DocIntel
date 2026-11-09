"use client";

import React, { useState, useEffect } from "react";
import type { PipelineRun, PipelineEvent } from "../types";
import {
  getPipelineEvents,
  retryPipelineRun,
  cancelPipelineRun,
} from "../api/pipeline.api";
import { PipelineGraph } from "./PipelineGraph";
import { PipelineStageCard } from "./PipelineStageCard";
import { PipelineEventLog } from "./PipelineEventLog";
import { RotateCcw, XCircle } from "lucide-react";

export interface PipelineDetailProps {
  initialRun: PipelineRun;
}

export const PipelineDetail: React.FC<PipelineDetailProps> = ({ initialRun }) => {
  const [run, setRun] = useState<PipelineRun>(initialRun);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [selectedStageId, setSelectedStageId] = useState<string>(
    initialRun.stages[0]?.id || "",
  );
  const [isRetrying, setIsRetrying] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    getPipelineEvents(run.id).then(setEvents);
  }, [run.id]);

  const selectedStage =
    run.stages.find((s) => s.id === selectedStageId) || run.stages[0];

  const handleRetry = async () => {
    setIsRetrying(true);
    setActionMessage(null);
    try {
      const res = await retryPipelineRun(run.id);
      setActionMessage(res.message);
      // update local run state to running/pending
      setRun((prev) => ({
        ...prev,
        status: "running",
        attempt: prev.attempt + 1,
      }));
    } finally {
      setIsRetrying(false);
    }
  };

  const handleCancel = async () => {
    setActionMessage(null);
    try {
      const res = await cancelPipelineRun(run.id);
      setActionMessage(res.message);
      setRun((prev) => ({ ...prev, status: "cancelled" }));
    } catch {
      //
    }
  };

  return (
    <div className="space-y-6">
      {/* Run Header Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-lg font-bold text-slate-900 font-mono">{run.id}</h2>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
                run.status === "completed"
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  : run.status === "running"
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : run.status === "failed"
                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                  : "bg-slate-100 text-slate-700"
              }`}
            >
              {run.status}
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Resource: <span className="font-semibold text-slate-800">{run.resourceTitle}</span> ({run.resourceId}) · Attempt {run.attempt} of {run.maxAttempts}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {run.status === "failed" && (
            <button
              type="button"
              onClick={handleRetry}
              disabled={isRetrying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium cursor-pointer shadow-xs disabled:opacity-50"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isRetrying ? "animate-spin" : ""}`} aria-hidden="true" />
              <span>Retry Pipeline</span>
            </button>
          )}

          {run.status === "running" && (
            <button
              type="button"
              onClick={handleCancel}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-medium cursor-pointer"
            >
              <XCircle className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Cancel Job</span>
            </button>
          )}
        </div>
      </div>

      {actionMessage && (
        <div role="status" className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900">
          {actionMessage}
        </div>
      )}

      {/* DAG Graph */}
      <PipelineGraph
        stages={run.stages}
        selectedStageId={selectedStageId}
        onSelectStage={setSelectedStageId}
      />

      {/* Selected Stage Detail Card */}
      {selectedStage && <PipelineStageCard stage={selectedStage} />}

      {/* Audit Transition Events */}
      <PipelineEventLog events={events} />
    </div>
  );
};
