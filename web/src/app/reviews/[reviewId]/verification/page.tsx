"use client";

import React, { use, useEffect } from "react";
import Link from "next/link";
import { FactVerificationPanel } from "@/features/governance/components";
import { useGovernanceDetail } from "@/features/governance/hooks/useGovernance";
import { submitVerificationAsDecision } from "@/features/governance/api/verification.api";
import { ErrorState } from "@/components/error-state";
import type { FactVerificationInput } from "@/features/governance/schemas/verification.schema";

interface PageProps {
  params: Promise<{ reviewId: string }>;
}

function VerificationContent({ params }: PageProps) {
  const { reviewId } = use(params);
  const { item, loading, submitting, error, reload } = useGovernanceDetail(reviewId);

  useEffect(() => {
    reload();
  }, [reload]);

  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-gray-600">Loading verification details...</p>
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="space-y-4">
        <Link href={`/reviews/${encodeURIComponent(reviewId)}`} className="text-sm font-medium text-blue-600 hover:underline">
          &larr; Back to Review Item
        </Link>
        <ErrorState title="Verification Unavailable" message={error} onRetry={reload} />
      </div>
    );
  }

  if (!item) return null;

  async function handleRecordVerification(
    verificationInput: FactVerificationInput,
    correctedValue?: string,
  ) {
    if (!item) return;
    await submitVerificationAsDecision({
      reviewItem: item,
      verificationInput,
      correctedValue,
    });
    await reload();
  }

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
        <span className="text-gray-900 font-medium">Fact Verification</span>
      </div>

      <FactVerificationPanel
        item={item}
        onRecordVerification={handleRecordVerification}
        disabled={submitting}
      />
    </div>
  );
}

export default function VerificationPage(props: PageProps) {
  return (
    <React.Suspense fallback={<div className="p-8 text-center text-gray-500">Loading...</div>}>
      <VerificationContent {...props} />
    </React.Suspense>
  );
}
