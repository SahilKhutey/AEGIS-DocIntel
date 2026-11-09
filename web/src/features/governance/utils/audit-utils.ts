import type { AuditEvent } from "../types";

export function formatAuditAction(action: string): { label: string; color: string } {
  switch (action.toLowerCase()) {
    case "create":
      return { label: "Created", color: "text-gray-700 bg-gray-100" };
    case "claim":
      return { label: "Claimed", color: "text-blue-700 bg-blue-100" };
    case "approve":
      return { label: "Approved", color: "text-emerald-700 bg-emerald-100" };
    case "correct":
      return { label: "Corrected", color: "text-purple-700 bg-purple-100" };
    case "reject":
      return { label: "Rejected", color: "text-rose-700 bg-rose-100" };
    case "request_evidence":
      return { label: "Evidence Requested", color: "text-orange-700 bg-orange-100" };
    case "reopen":
      return { label: "Reopened", color: "text-amber-800 bg-amber-100" };
    default:
      return { label: action.toUpperCase(), color: "text-gray-700 bg-gray-100" };
  }
}

export function formatTimestamp(isoString: string): string {
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export function sortAuditEvents(events: AuditEvent[], order: "asc" | "desc" = "asc"): AuditEvent[] {
  return [...events].sort((a, b) => {
    return order === "asc" ? a.sequence - b.sequence : b.sequence - a.sequence;
  });
}
