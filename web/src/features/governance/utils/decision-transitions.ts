import type { ReviewStatus, ReviewAction } from "../types";

/**
 * Validates which governance actions are permitted given the current review status,
 * mirroring backend authorization policies from src/engines/governance/policy.py.
 */

export function isTerminalStatus(status: ReviewStatus): boolean {
  return status === "approved" || status === "corrected" || status === "rejected";
}

export function getProposedAllowedDecisions(status: ReviewStatus): ReviewAction[] {
  switch (status) {
    case "pending":
    case "needs_evidence":
      return ["claim"];
    case "in_review":
      return ["approve", "correct", "reject", "request_evidence"];
    case "approved":
    case "corrected":
    case "rejected":
      return ["reopen"];
    default:
      return [];
  }
}

export function canExecuteAction(status: ReviewStatus, action: ReviewAction): boolean {
  const allowed = getProposedAllowedDecisions(status);
  return allowed.includes(action);
}

export function getTransitionTargetStatus(action: ReviewAction): ReviewStatus {
  switch (action) {
    case "claim":
    case "reopen":
      return "in_review";
    case "approve":
      return "approved";
    case "correct":
      return "corrected";
    case "reject":
      return "rejected";
    case "request_evidence":
      return "needs_evidence";
    case "create":
      return "pending";
    default:
      throw new Error(`Unknown review action: ${action}`);
  }
}
