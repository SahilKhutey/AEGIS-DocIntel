import { useState, useCallback, useRef } from "react";
import {
  fetchReviewQueue,
  fetchReviewItem,
  claimReviewItem,
  reopenReviewItem,
  fetchGovernanceMetrics,
} from "../api/review.api";
import {
  submitReviewDecision,
  submitReviewFeedback,
} from "../api/decision.api";
import { fetchReviewAuditHistory } from "../api/audit.api";
import type {
  ReviewItem,
  AuditEvent,
  GovernanceMetrics,
  ReviewQueueFiltersState,
  DecisionSubmission,
} from "../types";
import { ApiError } from "@/lib/errors";

export function useGovernanceQueue() {
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

  const loadQueue = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchReviewQueue({
        status: filters.status !== "all" ? filters.status : undefined,
      });
      setReviews(res.items);

      try {
        const m = await fetchGovernanceMetrics();
        setMetrics(m);
      } catch {
        // Metrics optional
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }, [filters.status]);

  const filteredReviews = reviews.filter((item) => {
    // Status filter
    if (filters.status !== "all" && item.status.toLowerCase() !== filters.status.toLowerCase()) {
      return false;
    }
    // Candidate type filter
    if (filters.candidateType !== "all" && item.candidate_type !== filters.candidateType) {
      return false;
    }
    // Assignment filter
    if (filters.assignment === "unassigned" && item.assigned_to) {
      return false;
    }
    if (filters.assignment === "assigned" && !item.assigned_to) {
      return false;
    }
    // Search query
    if (filters.searchQuery.trim()) {
      const q = filters.searchQuery.toLowerCase();
      const subject = String(item.candidate_data?.subject || "").toLowerCase();
      const attribute = String(
        item.candidate_data?.attribute || item.candidate_id || item.field_name || "",
      ).toLowerCase();
      const docId = item.document_id.toLowerCase();
      const revId = item.review_id.toLowerCase();
      if (
        !subject.includes(q) &&
        !attribute.includes(q) &&
        !docId.includes(q) &&
        !revId.includes(q)
      ) {
        return false;
      }
    }
    return true;
  });

  return {
    reviews: filteredReviews,
    allReviews: reviews,
    metrics,
    loading,
    error,
    filters,
    setFilters,
    reload: loadQueue,
  };
}

export function useGovernanceDetail(reviewId: string) {
  const [item, setItem] = useState<ReviewItem | null>(null);
  const [history, setHistory] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [staleWarning, setStaleWarning] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const itemRef = useRef<ReviewItem | null>(null);
  itemRef.current = item;

  const idempotencyKeyRef = useRef<string>(
    `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
  );

  const loadItem = useCallback(
    async (isInitial?: boolean) => {
      try {
        if (typeof isInitial === "boolean" ? isInitial : !itemRef.current) {
          setLoading(true);
        }
        setError(null);
        setStaleWarning(false);
        const data = await fetchReviewItem(reviewId);
        setItem(data);

        try {
          const auditData = await fetchReviewAuditHistory(reviewId);
          setHistory(auditData);
        } catch {
          // Audit history optional
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load review item.");
      } finally {
        setLoading(false);
      }
    },
    [reviewId],
  );

  const reloadWrapper = useCallback(
    (isInitial?: boolean) => {
      return loadItem(typeof isInitial === "boolean" ? isInitial : false);
    },
    [loadItem],
  );

  const claim = useCallback(async () => {
    if (!item) return;
    try {
      setSubmitting(true);
      setError(null);
      const updated = await claimReviewItem(item.review_id, item.version);
      setItem(updated);
      setSuccessMessage("Review item claimed successfully.");
      await loadItem();
    } catch (err) {
      if (err instanceof ApiError && err.isConflict) {
        setStaleWarning(true);
      } else {
        setError(err instanceof ApiError ? err.message : "Failed to claim review item.");
      }
    } finally {
      setSubmitting(false);
    }
  }, [item, loadItem]);

  const submitDecision = useCallback(
    async (submission: DecisionSubmission) => {
      if (!item) return;
      try {
        setSubmitting(true);
        setError(null);
        setSuccessMessage(null);

        const res = await submitReviewDecision(
          item.review_id,
          submission,
          idempotencyKeyRef.current,
        );

        setItem(res.item as ReviewItem);
        setSuccessMessage(`Decision '${submission.action.toUpperCase()}' committed successfully.`);
        // Refresh idempotency key for next operation
        idempotencyKeyRef.current = `idem-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
        await loadItem();
      } catch (err) {
        if (err instanceof ApiError && err.isConflict) {
          setStaleWarning(true);
        } else {
          setError(err instanceof ApiError ? err.message : "Failed to commit governance decision.");
        }
        throw err;
      } finally {
        setSubmitting(false);
      }
    },
    [item, loadItem],
  );

  const reopen = useCallback(
    async (rationale: string) => {
      if (!item) return;
      try {
        setSubmitting(true);
        setError(null);
        const res = await reopenReviewItem(item.review_id, item.version, rationale);
        setItem(res.item);
        setSuccessMessage("Review reopened successfully.");
        await loadItem();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to reopen review item.");
        throw err;
      } finally {
        setSubmitting(false);
      }
    },
    [item, loadItem],
  );

  const sendFeedback = useCallback(
    async (category: "wrong_value" | "wrong_attribute" | "bad_evidence" | "hallucination" | "missing_context" | "other", notes: string) => {
      if (!item) return;
      try {
        setSubmitting(true);
        await submitReviewFeedback(item.review_id, { category, notes });
        setSuccessMessage("Feedback recorded for benchmark evaluation.");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to submit feedback.");
      } finally {
        setSubmitting(false);
      }
    },
    [item],
  );

  return {
    item,
    history,
    loading,
    submitting,
    error,
    staleWarning,
    successMessage,
    reload: reloadWrapper,
    claim,
    submitDecision,
    reopen,
    sendFeedback,
    setSuccessMessage,
    setError,
  };
}
