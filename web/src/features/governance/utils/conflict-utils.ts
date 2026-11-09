import type { ConflictResolutionOutcome } from "../types";

export interface ConflictResolutionStyle {
  label: string;
  description: string;
  badgeBg: string;
  badgeText: string;
}

export const CONFLICT_RESOLUTION_CONFIG: Record<
  ConflictResolutionOutcome,
  ConflictResolutionStyle
> = {
  accepted_first_fact: {
    label: "Accept Fact 1 (Source A)",
    description: "Determined that the claim in Source A supersedes or corrects Source B.",
    badgeBg: "bg-blue-50",
    badgeText: "text-blue-700",
  },
  accepted_second_fact: {
    label: "Accept Fact 2 (Source B)",
    description: "Determined that the claim in Source B supersedes or corrects Source A.",
    badgeBg: "bg-indigo-50",
    badgeText: "text-indigo-700",
  },
  both_valid: {
    label: "Reconcile / Both Valid",
    description: "Both facts represent valid statements under different scopes, dates, or reporting bases.",
    badgeBg: "bg-purple-50",
    badgeText: "text-purple-700",
  },
  insufficient_evidence: {
    label: "Insufficient Evidence",
    description: "Neither claim has enough corroborated evidence to establish truth.",
    badgeBg: "bg-orange-50",
    badgeText: "text-orange-700",
  },
  escalated: {
    label: "Escalate for Compliance Review",
    description: "Severe material discrepancy requiring legal, risk, or compliance investigation.",
    badgeBg: "bg-rose-50",
    badgeText: "text-rose-700",
  },
};
