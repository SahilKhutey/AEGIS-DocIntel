import type { ReviewStatus, ReviewPriority } from "../types";

export interface StatusStyle {
  label: string;
  bg: string;
  text: string;
  border: string;
  dot: string;
}

export const REVIEW_STATUS_CONFIG: Record<ReviewStatus, StatusStyle> = {
  pending: {
    label: "Pending",
    bg: "bg-amber-50",
    text: "text-amber-800",
    border: "border-amber-200",
    dot: "bg-amber-500",
  },
  in_review: {
    label: "In Review",
    bg: "bg-blue-50",
    text: "text-blue-800",
    border: "border-blue-200",
    dot: "bg-blue-500",
  },
  approved: {
    label: "Approved",
    bg: "bg-emerald-50",
    text: "text-emerald-800",
    border: "border-emerald-200",
    dot: "bg-emerald-500",
  },
  corrected: {
    label: "Corrected",
    bg: "bg-purple-50",
    text: "text-purple-800",
    border: "border-purple-200",
    dot: "bg-purple-500",
  },
  rejected: {
    label: "Rejected",
    bg: "bg-rose-50",
    text: "text-rose-800",
    border: "border-rose-200",
    dot: "bg-rose-500",
  },
  needs_evidence: {
    label: "Needs Evidence",
    bg: "bg-orange-50",
    text: "text-orange-800",
    border: "border-orange-200",
    dot: "bg-orange-500",
  },
};

export function getStatusStyle(status: string): StatusStyle {
  const normalized = status.toLowerCase() as ReviewStatus;
  return (
    REVIEW_STATUS_CONFIG[normalized] || {
      label: status.replace(/_/g, " "),
      bg: "bg-gray-50",
      text: "text-gray-800",
      border: "border-gray-200",
      dot: "bg-gray-400",
    }
  );
}

export const PRIORITY_CONFIG: Record<
  ReviewPriority,
  { label: string; bg: string; text: string; border: string }
> = {
  high: {
    label: "High Priority",
    bg: "bg-rose-50",
    text: "text-rose-700",
    border: "border-rose-200",
  },
  medium: {
    label: "Medium Priority",
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
  },
  low: {
    label: "Low Priority",
    bg: "bg-gray-50",
    text: "text-gray-700",
    border: "border-gray-200",
  },
};

export function calculatePriority(confidence?: number): ReviewPriority {
  if (confidence === undefined || confidence === null) return "medium";
  if (confidence < 0.7) return "high";
  if (confidence < 0.9) return "medium";
  return "low";
}
