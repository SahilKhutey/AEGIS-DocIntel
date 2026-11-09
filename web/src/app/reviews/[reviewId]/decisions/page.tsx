"use client";

import React, { use, useEffect } from "react";
import Link from "next/link";
import { DecisionPanel } from "@/features/governance/components";
import { useGovernanceDetail } from "@/features/governance/hooks/useGovernance";
import { ErrorState } from "@/components/error-state";

interface PageProps {
  params: Promise<{ reviewId: string }>;
}

function DecisionsContent({ params }: PageProps) {
  const { reviewId } = use(params);
  const { item, loading, submitting, error, reload, claim, submitDecision, reopen } =
    useGovernanceDetail(reviewId);

  useEffect(() => {
    reload();
  }, [reload]);

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-gray-600">Loading decision workspace...</p>
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="space-y-4">
        <Link href={`/reviews/${encodeURIComponent(reviewId)}`} className="text-sm font-medium text-blue-600 hover:underline">
          &larr; Back to Review Item
        </Link>
        <ErrorState title="Decision Panel Unavailable" message={error} onRetry={reload} />
      </div>
    );
  }

  if (!item) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link href="/reviews" className="hover:text-blue-600">
          Review Queue
        </Link>
        <span>/</span>
        <Link href={`/reviews/${encodeURIComponent(reviewId)}`} className="hover:text-blue-600">
          {item.candidate_id}
        </Link>
        <span>/</span>
        <span className="text-gray-900 font-medium">Decisions</span>
      </div>

      <DecisionPanel
        item={item}
        onSubmitDecision={submitDecision}
        onClaim={claim}
        onReopen={reopen}
        submitting={submitting}
      />
    </div>
  );
}

export default function DecisionsPage(props: PageProps) {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-gray-500">Loading...</div>}>
      <DecisionsContent {...props} />
    </React.Suspense>
  );
}
