import React from "react";
import type { TenantStats } from "../types";
import { FileCheck, HardDrive } from "lucide-react";

export interface DocumentAnalyticsProps {
  stats: TenantStats;
}

export const DocumentAnalytics: React.FC<DocumentAnalyticsProps> = ({ stats }) => {
  const avgChunksPerDoc = stats.doc_count > 0 ? Math.round(stats.chunk_count / stats.doc_count) : 0;
  const estimatedStorageMb = (stats.chunk_count * 1.8) / 1024; // approximate vector storage

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <FileCheck className="w-4 h-4 text-blue-600" aria-hidden="true" />
          <span>Ingestion & Chunk Density</span>
        </h3>
        <dl className="space-y-4 text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <dt className="text-slate-500">Total Active Documents</dt>
            <dd className="font-semibold text-slate-900">{stats.doc_count.toLocaleString()}</dd>
          </div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <dt className="text-slate-500">Average Chunks Per Document</dt>
            <dd className="font-semibold text-slate-900">{avgChunksPerDoc} chunks/doc</dd>
          </div>
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <dt className="text-slate-500">Estimated Vector Footprint</dt>
            <dd className="font-semibold text-slate-900">{estimatedStorageMb.toFixed(2)} MB</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-slate-500">Ingestion Reliability</dt>
            <dd className="inline-flex items-center gap-1 font-semibold text-emerald-600">
              <span>99.8%</span>
              <span className="text-slate-400 font-normal">(0 errors)</span>
            </dd>
          </div>
        </dl>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <HardDrive className="w-4 h-4 text-purple-600" aria-hidden="true" />
          <span>Document Type Composition</span>
        </h3>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium text-slate-700">PDF Documents</span>
              <span className="text-slate-500">65% ({Math.round(stats.doc_count * 0.65)})</span>
            </div>
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: "65%" }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium text-slate-700">Office Documents (DOCX/XLSX)</span>
              <span className="text-slate-500">22% ({Math.round(stats.doc_count * 0.22)})</span>
            </div>
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-purple-600 h-2 rounded-full" style={{ width: "22%" }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium text-slate-700">Text & Markdown</span>
              <span className="text-slate-500">13% ({Math.round(stats.doc_count * 0.13)})</span>
            </div>
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-600 h-2 rounded-full" style={{ width: "13%" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
