"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ReviewQueue,
  ReviewQueueFilters,
  GovernanceMetricsBanner,
} from "@/features/governance/components";
import { fetchReviewQueue, fetchGovernanceMetrics } from "@/features/governance/api/review.api";
import type { ReviewItem, GovernanceMetrics, ReviewQueueFiltersState } from "@/features/governance/types";
import { ErrorState } from "@/components/error-state";
import { ApiError } from "@/lib/errors";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<ReviewQueueFiltersState>({
    status: "all",
    candidateType: "all",
    assignment: "all",
    searchQuery: "",
    sortBy: "updated_at",
    sortOrder: "desc",
  });

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load review queue
      const queueData = await fetchReviewQueue();
      setReviews(queueData.items || []);

      // Load metrics
      try {
        const metricsData = await fetchGovernanceMetrics();
        setMetrics(metricsData);
      } catch {
        // Metrics optional
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Compute status counts for filter tabs
  const countsByStatus = React.useMemo(() => {
    const counts: Record<string, number> = { all: reviews.length };
    reviews.forEach((r) => {
      const s = r.status.toLowerCase();
      counts[s] = (counts[s] || 0) + 1;
    });
    return counts;
  }, [reviews]);

  // Apply filters client-side
  const filteredReviews = reviews.filter((item) => {
    if (filters.status !== "all" && item.status.toLowerCase() !== filters.status.toLowerCase()) {
      return false;
    }
    if (filters.candidateType !== "all" && item.candidate_type !== filters.candidateType) {
      return false;
    }
    if (filters.assignment === "unassigned" && item.assigned_to) {
      return false;
    }
    if (filters.assignment === "assigned" && !item.assigned_to) {
      return false;
    }
    if (filters.searchQuery.trim()) {
      const q = filters.searchQuery.toLowerCase();
      const subject = String(item.candidate_data?.subject || "").toLowerCase();
      const attr = String(
        item.candidate_data?.attribute || item.candidate_id || item.field_name || "",
      ).toLowerCase();
      const doc = item.document_id.toLowerCase();
      const revId = item.review_id.toLowerCase();
      if (!subject.includes(q) && !attr.includes(q) && !doc.includes(q) && !revId.includes(q)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="space-y-8" data-testid="governance-reviews-page">
      {/* Header - Strictly preserves workbench.spec.ts heading matcher */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">
            Human Governance Review Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Review candidate facts, verify source evidence citations, resolve cross-document contradictions, and maintain tamper-evident audit history.
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
      <GovernanceMetricsBanner metrics={metrics} />

      {/* Filters Bar */}
      <ReviewQueueFilters
        filters={filters}
        onChange={(updated) => setFilters((prev) => ({ ...prev, ...updated }))}
        countsByStatus={countsByStatus}
      />

      {error && <ErrorState title="Queue Error" message={error} onRetry={loadData} />}

      {/* Items List */}
      <ReviewQueue items={filteredReviews} loading={loading} />
    </div>
  );
}
