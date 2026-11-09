"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchReviewQueue } from "@/features/governance/api/review.api";
import { fetchReviewAuditHistory } from "@/features/governance/api/audit.api";
import type { AuditEvent } from "@/features/governance/types";
import { formatAuditAction, formatTimestamp } from "@/features/governance/utils/audit-utils";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";
import { ApiError } from "@/lib/errors";

interface EnrichedAuditEvent extends AuditEvent {
  candidate_id?: string;
}

export default function GovernanceAuditPage() {
  const [events, setEvents] = useState<EnrichedAuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");

  const loadAllAuditEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch active reviews to inspect audit logs
      const queue = await fetchReviewQueue();
      const allEvents: EnrichedAuditEvent[] = [];

      for (const item of queue.items) {
        try {
          const itemEvents = await fetchReviewAuditHistory(item.review_id);
          itemEvents.forEach((ev) => {
            allEvents.push({
              ...ev,
              candidate_id: item.candidate_id,
            });
          });
        } catch {
          // Individual item audit fetch non-fatal
        }
      }

      // Sort globally by timestamp descending
      allEvents.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      setEvents(allEvents);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load governance audit logs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAllAuditEvents();
  }, [loadAllAuditEvents]);

  const filteredEvents = events.filter((ev) => {
    if (actionFilter !== "all" && ev.action.toLowerCase() !== actionFilter.toLowerCase()) {
      return false;
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const revId = ev.review_id.toLowerCase();
      const actor = ev.actor_id.toLowerCase();
      const candidate = (ev.candidate_id || "").toLowerCase();
      const rationale = ev.rationale.toLowerCase();
      if (!revId.includes(q) && !actor.includes(q) && !candidate.includes(q) && !rationale.includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-6" data-testid="governance-audit-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Governance Audit Log
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Tamper-evident, append-only record of all human-in-the-loop governance decisions, fact verifications, and conflict resolutions.
          </p>
        </div>
        <button
          type="button"
          onClick={loadAllAuditEvents}
          className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50"
        >
          Refresh Logs
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search by review ID, actor, candidate ID, or rationale..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-gray-300 pl-9 pr-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
          />
          <svg
            className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            aria-label="Filter by action"
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none"
          >
            <option value="all">All Actions</option>
            <option value="approve">Approve</option>
            <option value="correct">Correct</option>
            <option value="reject">Reject</option>
            <option value="request_evidence">Request Evidence</option>
            <option value="claim">Claim</option>
            <option value="reopen">Reopen</option>
          </select>
        </div>
      </div>

      {error && <ErrorState title="Audit Error" message={error} onRetry={loadAllAuditEvents} />}

      {loading ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
          <p className="mt-4 text-sm font-medium text-gray-600">Loading audit records...</p>
        </div>
      ) : filteredEvents.length === 0 ? (
        <EmptyState
          title="No audit events found"
          description="No governance audit records match your query or filter criteria."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Review Item</th>
                  <th scope="col" className="px-6 py-3.5">Timestamp</th>
                  <th scope="col" className="px-6 py-3.5">Actor</th>
                  <th scope="col" className="px-6 py-3.5">Action</th>
                  <th scope="col" className="px-6 py-3.5">Status Transition</th>
                  <th scope="col" className="px-6 py-3.5">Version</th>
                  <th scope="col" className="px-6 py-3.5">Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono text-xs">
                {filteredEvents.map((ev) => {
                  const actionMeta = formatAuditAction(ev.action);
                  return (
                    <tr key={ev.event_id} className="hover:bg-gray-50/75 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-900 font-sans max-w-xs truncate">
                        <Link
                          href={`/reviews/${encodeURIComponent(ev.review_id)}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline font-semibold"
                        >
                          {ev.candidate_id || ev.review_id}
                        </Link>
                        <p className="text-xs text-gray-400 font-mono truncate">{ev.review_id}</p>
                      </td>
                      <td className="px-6 py-4 text-gray-500 whitespace-nowrap font-sans">
                        {formatTimestamp(ev.timestamp)}
                      </td>
                      <td className="px-6 py-4 text-gray-900 font-medium font-sans">{ev.actor_id}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex rounded px-2 py-0.5 text-[11px] font-semibold uppercase font-sans ${actionMeta.color}`}
                        >
                          {actionMeta.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-gray-500">{ev.previous_status}</span>
                        <span className="mx-1 text-gray-400">&rarr;</span>
                        <span className="font-semibold text-gray-900">{ev.new_status}</span>
                      </td>
                      <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                        v{ev.previous_version} &rarr; v{ev.new_version}
                      </td>
                      <td className="px-6 py-4 font-sans text-xs text-gray-700 max-w-xs truncate">
                        {ev.rationale || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
