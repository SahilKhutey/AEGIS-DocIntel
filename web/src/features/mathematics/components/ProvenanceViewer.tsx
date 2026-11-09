import React from "react";
import type { RepresentationProvenance } from "../types";
import { ShieldCheck, GitBranch, Cpu, Calendar, Hash } from "lucide-react";

export interface ProvenanceViewerProps {
  provenance: RepresentationProvenance;
}

export const ProvenanceViewer: React.FC<ProvenanceViewerProps> = ({ provenance }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2">
        <ShieldCheck className="w-4 h-4 text-emerald-600" aria-hidden="true" />
        <h3 className="text-sm font-bold text-slate-900">Mathematical Provenance</h3>
      </div>

      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-500 flex items-center gap-1.5 mb-1">
            <GitBranch className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Source Document</span>
          </dt>
          <dd className="font-semibold text-slate-800">
            {provenance.sourceDocumentTitle}
            <span className="block text-[10px] text-slate-400 font-mono font-normal">{provenance.sourceDocumentId}</span>
          </dd>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-500 flex items-center gap-1.5 mb-1">
            <Cpu className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Inference Model & Pooling</span>
          </dt>
          <dd className="font-semibold text-slate-800 font-mono">
            {provenance.model}
            <span className="block text-[10px] text-slate-400 font-sans font-normal">{provenance.poolingMethod}</span>
          </dd>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-500 flex items-center gap-1.5 mb-1">
            <Hash className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Cryptographic Checksum</span>
          </dt>
          <dd className="font-mono text-[11px] text-slate-800 break-all">{provenance.checksum}</dd>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
          <dt className="text-slate-500 flex items-center gap-1.5 mb-1">
            <Calendar className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Generated At</span>
          </dt>
          <dd className="font-semibold text-slate-800">
            {new Date(provenance.generatedAt).toLocaleString()}
          </dd>
        </div>
      </dl>
    </div>
  );
};
