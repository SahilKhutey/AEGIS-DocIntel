"use client";

import React, { Suspense } from "react";
import { ProcessingMonitor } from "@/features/processing/components/processing-monitor";

export default function ProcessingPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-12 text-center" aria-busy="true">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-[var(--primary)] border-r-transparent" />
          <p className="mt-4 text-sm font-medium text-[var(--muted)]">Loading processing telemetry...</p>
        </div>
      }
    >
      <div className="space-y-6">
        <ProcessingMonitor />
      </div>
    </Suspense>
  );
}
