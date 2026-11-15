import React from "react";
import type { ThroughputMetrics } from "../types";
import { Activity } from "lucide-react";

export interface ThroughputChartProps {
  metrics: ThroughputMetrics;
}

export const ThroughputChart: React.FC<ThroughputChartProps> = ({ metrics }) => {
  const workerUtilizationPct = Math.round((metrics.activeWorkers / metrics.maxWorkers) * 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
        <Activity className="w-4 h-4 text-emerald-600" aria-hidden="true" />
        <h3 className="text-sm font-bold text-slate-900">Throughput & Worker Concurrency</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] uppercase font-semibold text-slate-600 block mb-1">
            Request Rate
          </span>
          <div className="text-xl font-bold text-slate-800 font-mono">
            {metrics.requestsPerMinute} <span className="text-xs font-normal text-slate-500 font-sans">RPM</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] uppercase font-semibold text-slate-600 block mb-1">
            Chunk Ingestion Rate
          </span>
          <div className="text-xl font-bold text-slate-800 font-mono">
            {metrics.chunksPerSecond} <span className="text-xs font-normal text-slate-500 font-sans">chunks/s</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] uppercase font-semibold text-slate-600 block mb-1">
            Worker Pool
          </span>
          <div className="text-xl font-bold text-slate-800 font-mono">
            {metrics.activeWorkers}/{metrics.maxWorkers} <span className="text-xs font-normal text-slate-500 font-sans">active</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] uppercase font-semibold text-slate-600 block mb-1">
            Pending Queue Depth
          </span>
          <div className="text-xl font-bold text-slate-800 font-mono">
            {metrics.queueDepth} <span className="text-xs font-normal text-slate-500 font-sans">jobs</span>
          </div>
        </div>
      </div>

      <div className="space-y-1.5 pt-2">
        <div className="flex justify-between text-xs font-medium">
          <span className="text-slate-600">Worker Pool Capacity</span>
          <span className="text-slate-900 font-mono">{workerUtilizationPct}% ({metrics.activeWorkers} of {metrics.maxWorkers})</span>
        </div>
        <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
          <div
            className="bg-emerald-500 h-2 rounded-full transition-all"
            style={{ width: `${workerUtilizationPct}%` }}
          />
        </div>
      </div>
    </div>
  );
};
