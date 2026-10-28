import React from "react";

export type StatusType =
  | "pending"
  | "indexing"
  | "ready"
  | "failed"
  | "reindexing"
  | "in_review"
  | "approved"
  | "corrected"
  | "rejected"
  | "needs_evidence"
  | "conflict"
  | "match";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string; dot: string }> = {
  // Document statuses
  pending: { bg: "bg-amber-100", text: "text-amber-800", label: "Pending", dot: "bg-amber-500" },
  indexing: { bg: "bg-blue-100", text: "text-blue-800", label: "Indexing", dot: "bg-blue-500" },
  ready: { bg: "bg-emerald-100", text: "text-emerald-800", label: "Ready", dot: "bg-emerald-500" },
  failed: { bg: "bg-rose-100", text: "text-rose-800", label: "Failed", dot: "bg-rose-500" },
  reindexing: { bg: "bg-indigo-100", text: "text-indigo-800", label: "Reindexing", dot: "bg-indigo-500" },

  // Review statuses
  in_review: { bg: "bg-sky-100", text: "text-sky-800", label: "In Review", dot: "bg-sky-500" },
  approved: { bg: "bg-emerald-100", text: "text-emerald-800", label: "Approved", dot: "bg-emerald-500" },
  corrected: { bg: "bg-purple-100", text: "text-purple-800", label: "Corrected", dot: "bg-purple-500" },
  rejected: { bg: "bg-rose-100", text: "text-rose-800", label: "Rejected", dot: "bg-rose-500" },
  needs_evidence: { bg: "bg-orange-100", text: "text-orange-800", label: "Needs Evidence", dot: "bg-orange-500" },

  // Intelligence comparison
  conflict: { bg: "bg-rose-100", text: "text-rose-800", label: "Conflict Detected", dot: "bg-rose-500" },
  match: { bg: "bg-emerald-100", text: "text-emerald-800", label: "Aligned", dot: "bg-emerald-500" },
};

export function StatusBadge({ status, size = "md" }: StatusBadgeProps) {
  const norm = status.toLowerCase();
  const cfg = STATUS_STYLES[norm] || {
    bg: "bg-gray-100",
    text: "text-gray-800",
    label: status,
    dot: "bg-gray-400",
  };

  const pad = size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs sm:text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${cfg.bg} ${cfg.text} ${pad}`}
      role="status"
      aria-label={`Status: ${cfg.label}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} aria-hidden="true" />
      <span>{cfg.label}</span>
    </span>
  );
}
