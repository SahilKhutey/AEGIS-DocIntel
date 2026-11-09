"use client";

import React, { useState } from "react";
import type { VectorRepresentation } from "../types";
import { List, Grid, ChevronLeft, ChevronRight } from "lucide-react";

export interface VectorViewerProps {
  vector: VectorRepresentation;
  chunkSize?: number;
}

export const VectorViewer: React.FC<VectorViewerProps> = ({
  vector,
  chunkSize = 32,
}) => {
  const [viewMode, setViewMode] = useState<"heatmap" | "table">("heatmap");
  const [currentPage, setCurrentPage] = useState(0);

  const totalElements = vector.values.length;
  const totalPages = Math.max(1, Math.ceil(totalElements / chunkSize));
  const startIndex = currentPage * chunkSize;
  const currentChunk = vector.values.slice(startIndex, startIndex + chunkSize);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-5">
      {/* Header and Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900">{vector.name}</h3>
          <p className="text-xs text-slate-500">
            {vector.dimensions} dimensions · {vector.precision} · L2 Norm: {vector.l2Norm.toFixed(4)}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs">
            <button
              type="button"
              onClick={() => setViewMode("heatmap")}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === "heatmap" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
              } cursor-pointer`}
              aria-label="Heatmap view"
            >
              <Grid className="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
              Heatmap
            </button>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                viewMode === "table" ? "bg-white text-slate-900 shadow-xs" : "text-slate-600 hover:text-slate-900"
              } cursor-pointer`}
              aria-label="Table view"
            >
              <List className="w-3.5 h-3.5 inline mr-1" aria-hidden="true" />
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Summary KPI Pills */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-semibold uppercase text-slate-400">Total Dimensions</span>
          <div className="text-base font-bold text-slate-800">{vector.dimensions.toLocaleString()}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-semibold uppercase text-slate-400">Min Value</span>
          <div className="text-base font-bold text-slate-800 font-mono">{vector.min.toFixed(4)}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-semibold uppercase text-slate-400">Max Value</span>
          <div className="text-base font-bold text-slate-800 font-mono">{vector.max.toFixed(4)}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <span className="text-[10px] font-semibold uppercase text-slate-400">Sparsity</span>
          <div className="text-base font-bold text-slate-800">{vector.sparsity}%</div>
        </div>
      </div>

      {/* Viewport: Heatmap or Table */}
      {viewMode === "heatmap" ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Dimensions [{startIndex}..{Math.min(startIndex + chunkSize - 1, totalElements - 1)}]</span>
            <div className="flex items-center gap-2">
              <span className="inline-block w-3 h-3 rounded bg-blue-500" />
              <span>Negative</span>
              <span className="inline-block w-3 h-3 rounded bg-emerald-500 ml-2" />
              <span>Positive</span>
            </div>
          </div>

          <div className="grid grid-cols-4 sm:grid-cols-8 md:grid-cols-16 gap-1.5 p-3 rounded-xl bg-slate-900 border border-slate-800">
            {currentChunk.map((val, idx) => {
              const dimIndex = startIndex + idx;
              const isPositive = val >= 0;
              const barHeightPct = Math.min(100, Math.round(Math.abs(val) * 800));
              return (
                <div
                  key={dimIndex}
                  className="group relative flex flex-col items-center justify-end h-16 rounded bg-slate-800/80 p-0.5 hover:ring-1 hover:ring-white transition-all cursor-pointer"
                  title={`Dim ${dimIndex}: ${val.toFixed(6)}`}
                >
                  <div
                    className={`w-full rounded-xs transition-all ${
                      isPositive ? "bg-emerald-400" : "bg-blue-400"
                    }`}
                    style={{ height: `${Math.max(10, barHeightPct)}%` }}
                  />
                  <span className="mt-1 text-[9px] font-mono text-slate-400 select-none">
                    {dimIndex}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
              <tr>
                <th className="px-3 py-2">Index</th>
                <th className="px-3 py-2">Value (Raw float32)</th>
                <th className="px-3 py-2">Sign</th>
                <th className="px-3 py-2">Normalized Magnitude</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {currentChunk.map((val, idx) => {
                const dimIndex = startIndex + idx;
                return (
                  <tr key={dimIndex} className="hover:bg-slate-50/60">
                    <td className="px-3 py-1.5 text-slate-500 font-sans">{dimIndex}</td>
                    <td className="px-3 py-1.5 font-bold">{val.toFixed(6)}</td>
                    <td className="px-3 py-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        val >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-blue-50 text-blue-700"
                      }`}>
                        {val >= 0 ? "+ Positive" : "- Negative"}
                      </span>
                    </td>
                    <td className="px-3 py-1.5 text-slate-500">
                      {Math.abs(val / (vector.max || 1)).toFixed(4)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
          <span>
            Viewing {startIndex + 1}–{Math.min(startIndex + chunkSize, totalElements)} of {totalElements} preview dimensions
          </span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={currentPage === 0}
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              aria-label="Previous dimensions"
            >
              <ChevronLeft className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <span className="px-2 font-medium text-slate-700">
              Page {currentPage + 1} of {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage >= totalPages - 1}
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              aria-label="Next dimensions"
            >
              <ChevronRight className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
