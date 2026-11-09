import React from "react";
import Link from "next/link";
import type { ReviewItem } from "../types";
import { getStatusStyle, calculatePriority, PRIORITY_CONFIG } from "../utils/review-status";
import { EmptyState } from "@/components/empty-state";

interface ReviewQueueProps {
  items: ReviewItem[];
  loading: boolean;
  onClaim?: (reviewId: string, version: number) => Promise<void>;
}

export function ReviewQueue({ items, loading }: ReviewQueueProps) {
  if (loading) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-12 text-center" aria-busy="true">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-gray-600">Loading review queue...</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Review queue is empty"
        description="There are currently no candidate facts or detected conflicts matching the selected filters."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 text-left text-sm" data-testid="review-queue-table">
          <thead className="bg-gray-50 text-xs font-semibold uppercase text-gray-500">
            <tr>
              <th scope="col" className="px-6 py-3.5">Candidate Subject &bull; Attribute</th>
              <th scope="col" className="px-6 py-3.5">Type</th>
              <th scope="col" className="px-6 py-3.5">Inferred Value</th>
              <th scope="col" className="px-6 py-3.5">Status</th>
              <th scope="col" className="px-6 py-3.5">Priority</th>
              <th scope="col" className="px-6 py-3.5">Version</th>
              <th scope="col" className="px-6 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item) => {
              const subject = String(item.candidate_data?.subject || "Fact");
              const candidateAttr =
                item.candidate_data?.attribute ||
                item.candidate_id ||
                item.field_name ||
                item.review_id;
              const attribute = String(candidateAttr);
              const value =
                item.current_revision?.corrected_value ??
                item.candidate_data?.value ??
                item.candidate_data?.raw_value ??
                item.extracted_value ??
                "—";
              const statusStyle = getStatusStyle(item.status);
              const priority = calculatePriority(
                item.confidence ??
                  (typeof item.candidate_data?.confidence === "number"
                    ? item.candidate_data.confidence
                    : undefined),
              );
              const priorityStyle = PRIORITY_CONFIG[priority];

              return (
                <tr key={item.review_id} className="hover:bg-gray-50/75 transition-colors">
                  <td className="px-6 py-4 font-medium text-gray-900 max-w-xs truncate">
                    <Link
                      href={`/reviews/${encodeURIComponent(item.review_id)}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {subject} &bull; {attribute}
                    </Link>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400 font-mono truncate">{item.review_id}</span>
                      {item.assigned_to && (
                        <span className="text-[10px] bg-gray-100 text-gray-600 rounded px-1.5 py-0.5">
                          {item.assigned_to}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex rounded px-2 py-0.5 text-xs font-mono uppercase ${
                        item.candidate_type === "conflict"
                          ? "bg-purple-100 text-purple-700 font-semibold"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {item.candidate_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-gray-800 max-w-xs truncate">
                    {String(value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${statusStyle.dot}`} />
                      {statusStyle.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex rounded px-2 py-0.5 text-xs font-medium border ${priorityStyle.bg} ${priorityStyle.text} ${priorityStyle.border}`}
                    >
                      {priorityStyle.label}
                    </span>
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
  );
}
