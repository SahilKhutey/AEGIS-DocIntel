"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ReviewListSchema,
  GovernanceMetricsSchema,
  type ReviewItem,
  type GovernanceMetrics,
} from "@/lib/schemas";
import { apiRequest } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";
import { StatusBadge } from "@/components/status-badge";
import { EmptyState } from "@/components/empty-state";
import { ErrorState } from "@/components/error-state";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    try {
      setLoading(true);
      setError(null);

      // Load review queue
      const queueData = await apiRequest("/api/v1/reviews", ReviewListSchema);
      setReviews(queueData.items || []);

      // Load metrics
      try {
        const metricsData = await apiRequest("/api/v1/reviews/metrics", GovernanceMetricsSchema);
        setMetrics(metricsData);
      } catch {
        // Metrics optional
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const filteredReviews = reviews.filter((item) => {
    if (statusFilter === "all") return true;
    return item.status.toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Human Governance Review Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Review extracted candidate facts, resolve cross-document contradictions, and maintain audit trails.
          </p>
        </div>
        <button
          type="button"
          onClick={loadData}
          className="inline-flex items-center rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-xs hover:bg-gray-50"
        >
          Refresh Queue
        </button>
      </div>

      {/* Metrics Banner */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Total Queue
            </span>
            <p className="mt-1 text-2xl font-bold text-gray-900">{metrics.total_items}</p>
          </div>
          <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
              Approval Rate
            </span>
            <p className="mt-1 text-2xl font-bold text-emerald-800">
              {(metrics.approval_rate * 100).toFixed(0)}%
            </p>
          </div>
          <div className="rounded-xl border border-purple-100 bg-purple-50/50 p-4 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-purple-700">
              Correction Rate
            </span>
            <p className="mt-1 text-2xl font-bold text-purple-800">
              {(metrics.correction_rate * 100).toFixed(0)}%
            </p>
          </div>
          <div className="rounded-xl border border-rose-100 bg-rose-50/50 p-4 shadow-xs">
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-700">
              Rejection Rate
            </span>
            <p className="mt-1 text-2xl font-bold text-rose-800">
              {(metrics.rejection_rate * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-gray-200 pb-3">
        {["all", "pending", "in_review", "approved", "corrected", "rejected", "needs_evidence"].map(
          (status) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(status)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium capitalize transition ${
                statusFilter === status
                  ? "bg-blue-600 text-white shadow-xs font-semibold"
                  : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
              }`}
            >
              {status.replace("_", " ")}
            </button>
          ),
        )}
      </div>

      {error && <ErrorState title="Queue Error" message={error} onRetry={loadData} />}

      {/* Main Review Items List */}
      {loading ? (
        <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
          <p className="mt-4 text-sm font-medium text-gray-600">Loading review queue...</p>
        </div>
      ) : reviews.length === 0 ? (
        <EmptyState
          title="Review queue is empty"
          description="There are currently no candidate facts or detected conflicts requiring human review."
        />
      ) : filteredReviews.length === 0 ? (
        <div className="rounded-xl border border-gray-200 bg-white p-8 text-center text-sm text-gray-500">
          No items match the selected status filter.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Candidate Subject &bull; Attribute</th>
                  <th scope="col" className="px-6 py-3.5">Type</th>
                  <th scope="col" className="px-6 py-3.5">Inferred Value</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5">Version</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredReviews.map((item) => {
                  const subject = String(item.candidate_data?.subject || "Fact");
                  const attribute = String(item.candidate_data?.attribute || item.candidate_id);
                  const value = item.current_revision?.corrected_value ?? item.candidate_data?.value ?? item.candidate_data?.raw_value;

                  return (
                    <tr key={item.review_id} className="hover:bg-gray-50/75 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-900 max-w-xs truncate">
                        <Link
                          href={`/reviews/${encodeURIComponent(item.review_id)}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {subject} &bull; {attribute}
                        </Link>
                        <p className="text-xs text-gray-400 font-mono truncate">{item.review_id}</p>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex rounded bg-gray-100 px-2 py-0.5 text-xs font-mono uppercase text-gray-600">
                          {item.candidate_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-gray-800 max-w-xs truncate">
                        {String(value)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                        v{item.version}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <Link
                          href={`/reviews/${encodeURIComponent(item.review_id)}`}
                          className="inline-flex items-center rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                        >
                          Review &rarr;
                        </Link>
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
