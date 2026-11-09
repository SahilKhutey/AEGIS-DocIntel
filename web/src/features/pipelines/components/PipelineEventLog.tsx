import React from "react";
import type { PipelineEvent } from "../types";
import { History, ArrowRight } from "lucide-react";

export interface PipelineEventLogProps {
  events: PipelineEvent[];
}

export const PipelineEventLog: React.FC<PipelineEventLogProps> = ({ events }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
      <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
        <History className="w-4 h-4 text-slate-600" aria-hidden="true" />
        <h3 className="text-sm font-bold text-slate-900">Chronological Event Trail</h3>
      </div>

      {events.length === 0 ? (
        <p className="text-xs text-slate-400 italic">No events recorded for this pipeline execution.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-3 py-2">Seq</th>
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Transition</th>
                <th className="px-3 py-2">Worker</th>
                <th className="px-3 py-2">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-mono text-[11px]">
              {events.map((evt) => (
                <tr key={evt.sequence} className="hover:bg-slate-50/50">
                  <td className="px-3 py-2 font-bold text-slate-400 font-sans">{evt.sequence}</td>
                  <td className="px-3 py-2 text-slate-500 whitespace-nowrap">
                    {new Date(evt.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1">
                      <span className="text-slate-500">{evt.fromStatus}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" aria-hidden="true" />
                      <span className="font-bold text-slate-900">{evt.toStatus}</span>
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500">{evt.workerId}</td>
                  <td className="px-3 py-2 font-sans text-slate-800">
                    {evt.message}
                    {evt.errorCode && (
                      <span className="ml-2 px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 text-[10px] font-mono font-bold">
                        {evt.errorCode}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
