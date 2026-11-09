import React, { useState } from "react";
import type { AuditEvent } from "../types";
import { formatAuditAction, formatTimestamp, sortAuditEvents } from "../utils/audit-utils";

interface AuditTimelineProps {
  events: AuditEvent[];
  title?: string;
}

export function AuditTimeline({
  events,
  title = "Append-Only Audit History",
}: AuditTimelineProps) {
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const sorted = sortAuditEvents(events, order);

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white shadow-xs overflow-hidden"
      data-testid="audit-timeline"
    >
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            {title} ({events.length})
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Tamper-evident, immutable audit trail of review transitions and rationale.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOrder(order === "desc" ? "asc" : "desc")}
            className="rounded border border-gray-200 px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-50 flex items-center gap-1"
          >
            <span>{order === "desc" ? "Newest First" : "Oldest First"}</span>
            <span className="font-mono">{order === "desc" ? "↓" : "↑"}</span>
          </button>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="p-8 text-center text-sm text-gray-500 italic">
          No audit events recorded yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
              <tr>
                <th scope="col" className="px-6 py-3">Seq</th>
                <th scope="col" className="px-6 py-3">Timestamp</th>
                <th scope="col" className="px-6 py-3">Actor</th>
                <th scope="col" className="px-6 py-3">Action</th>
                <th scope="col" className="px-6 py-3">Status Transition</th>
                <th scope="col" className="px-6 py-3">Version</th>
                <th scope="col" className="px-6 py-3">Audited Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 font-mono text-xs">
              {sorted.map((ev) => {
                const actionMeta = formatAuditAction(ev.action);
                return (
                  <tr key={ev.event_id} className="hover:bg-gray-50/75 transition-colors">
                    <td className="px-6 py-3 font-bold text-gray-600">#{ev.sequence}</td>
                    <td className="px-6 py-3 text-gray-500 whitespace-nowrap font-sans">
                      {formatTimestamp(ev.timestamp)}
                    </td>
                    <td className="px-6 py-3 text-gray-900 font-medium">{ev.actor_id}</td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex rounded px-2 py-0.5 text-[11px] font-semibold uppercase font-sans ${actionMeta.color}`}
                      >
                        {actionMeta.label}
                      </span>
                    </td>
                    <td className="px-6 py-3 whitespace-nowrap">
                      <span className="text-gray-500">{ev.previous_status}</span>
                      <span className="mx-1 text-gray-400">&rarr;</span>
                      <span className="font-semibold text-gray-900">{ev.new_status}</span>
                    </td>
                    <td className="px-6 py-3 text-gray-500">
                      v{ev.previous_version} &rarr; v{ev.new_version}
                    </td>
                    <td className="px-6 py-3 font-sans text-xs text-gray-700 max-w-sm truncate">
                      {ev.rationale || "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
