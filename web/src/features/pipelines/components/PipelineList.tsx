"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getPipelineRuns } from "../api/pipeline.api";
import type { PipelineRun, PipelineJobStatus } from "../types";
import { DataTable, type Column } from "@/components/advanced/DataTable";
import { CheckCircle2, AlertCircle, Clock, Search, RefreshCw, ChevronRight } from "lucide-react";

export const PipelineList: React.FC = () => {
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [statusFilter, setStatusFilter] = useState<PipelineJobStatus | "all">("all");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const loadRuns = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getPipelineRuns(statusFilter === "all" ? undefined : statusFilter);
      setRuns(data);
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadRuns();
  }, [loadRuns]);

  const filteredRuns = runs.filter((r) =>
    r.resourceTitle.toLowerCase().includes(search.toLowerCase()) ||
    r.id.toLowerCase().includes(search.toLowerCase()),
  );

  const columns: Column<PipelineRun>[] = [
    {
      key: "id",
      header: "Pipeline Run ID",
      sortable: true,
      render: (run) => (
        <Link
          href={`/pipelines/${run.id}`}
          className="font-mono font-bold text-blue-600 hover:underline flex items-center gap-1.5"
        >
          <span>{run.id}</span>
          <ChevronRight className="w-3 h-3 text-slate-400" aria-hidden="true" />
        </Link>
      ),
    },
    {
      key: "resourceTitle",
      header: "Source Resource",
      sortable: true,
      render: (run) => (
        <div>
          <span className="font-semibold text-slate-900 block">{run.resourceTitle}</span>
          <span className="text-[10px] text-slate-600 font-mono">{run.resourceId}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (run) => {
        let badgeColor = "bg-slate-100 text-slate-700";
        let Icon = Clock;
        if (run.status === "completed") {
          badgeColor = "bg-emerald-50 text-emerald-700 border border-emerald-200";
          Icon = CheckCircle2;
        } else if (run.status === "running") {
          badgeColor = "bg-blue-50 text-blue-700 border border-blue-200";
          Icon = RefreshCw;
        } else if (run.status === "failed") {
          badgeColor = "bg-rose-50 text-rose-700 border border-rose-200";
          Icon = AlertCircle;
        }
        return (
          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${badgeColor}`}>
            <Icon className={`w-3.5 h-3.5 ${run.status === "running" ? "animate-spin" : ""}`} aria-hidden="true" />
            <span>{run.status}</span>
          </span>
        );
      },
    },
    {
      key: "attempt",
      header: "Attempt",
      render: (run) => (
        <span className="font-mono text-xs text-slate-600">
          {run.attempt} / {run.maxAttempts}
        </span>
      ),
    },
    {
      key: "stages",
      header: "Stage Progress",
      render: (run) => {
        const completedStages = run.stages.filter((s) => s.status === "succeeded").length;
        const total = run.stages.length;
        const pct = total > 0 ? (completedStages / total) * 100 : 0;
        return (
          <div className="w-32">
            <div className="flex justify-between text-[10px] font-mono mb-1 text-slate-500">
              <span>{completedStages}/{total} stages</span>
              <span>{pct.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
              <div
                className={`h-1.5 rounded-full ${
                  run.status === "failed" ? "bg-rose-500" : "bg-blue-600"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      },
    },
    {
      key: "createdAt",
      header: "Started At",
      sortable: true,
      render: (run) => (
        <span className="text-slate-500 text-[11px]">
          {new Date(run.createdAt).toLocaleString()}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h2 className="text-lg font-bold text-slate-900">Pipeline Execution Runs</h2>
          <p className="text-xs text-slate-500">
            Monitor and trace asynchronous ingestion, extraction, vector representation, and indexing pipelines.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-3 text-slate-400 pointer-events-none" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search pipelines..."
              aria-label="Search pipelines"
              className="pl-8 pr-3 h-9 min-h-[36px] box-border text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={statusFilter}
            aria-label="Filter pipeline runs by status"
            onChange={(e) => setStatusFilter(e.target.value as PipelineJobStatus | "all")}
            className="px-3 h-9 min-h-[36px] box-border text-xs rounded-lg border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="all">All Statuses</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>

          <button
            type="button"
            onClick={loadRuns}
            disabled={isLoading}
            className="h-9 w-9 min-h-[36px] min-w-[36px] box-border flex items-center justify-center rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-50 cursor-pointer text-slate-600"
            title="Refresh runs"
            aria-label="Refresh pipeline runs"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-blue-600" : ""}`} aria-hidden="true" />
          </button>
        </div>
      </div>

      {/* Table */}
      <DataTable
        data={filteredRuns}
        columns={columns}
        keyExtractor={(item) => item.id}
      />
    </div>
  );
};
