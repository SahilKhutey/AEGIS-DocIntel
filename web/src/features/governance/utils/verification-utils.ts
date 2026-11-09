import type { FactVerificationStatus, DecisionType } from "../types";

export interface VerificationStyle {
  label: string;
  description: string;
  badgeBg: string;
  badgeText: string;
  border: string;
}

export const VERIFICATION_CONFIG: Record<FactVerificationStatus, VerificationStyle> = {
  verified: {
    label: "Fully Verified",
    description: "The extracted fact is explicitly confirmed by the authoritative source text.",
    badgeBg: "bg-emerald-50",
    badgeText: "text-emerald-700",
    border: "border-emerald-300",
  },
  partially_verified: {
    label: "Partially Verified",
    description: "The fact is supported in substance, but attributes, units, or precision need human correction.",
    badgeBg: "bg-blue-50",
    badgeText: "text-blue-700",
    border: "border-blue-300",
  },
  not_verified: {
    label: "Not Verified",
    description: "The cited source passage does not substantiate this claim or inference.",
    badgeBg: "bg-rose-50",
    badgeText: "text-rose-700",
    border: "border-rose-300",
  },
  contradicted: {
    label: "Contradicted",
    description: "The source passage explicitly refutes the extracted value or relationship.",
    badgeBg: "bg-rose-100",
    badgeText: "text-rose-800",
    border: "border-rose-400",
  },
  insufficient_evidence: {
    label: "Insufficient Evidence",
    description: "Additional context, missing document pages, or clarifying queries are needed.",
    badgeBg: "bg-orange-50",
    badgeText: "text-orange-700",
    border: "border-orange-300",
  },
};

/**
 * Maps a verification outcome to a recommended formal governance decision.
 */
export function mapVerificationToDecision(status: FactVerificationStatus): DecisionType {
  switch (status) {
    case "verified":
      return "approve";
    case "partially_verified":
      return "correct";
    case "not_verified":
    case "contradicted":
      return "reject";
    case "insufficient_evidence":
      return "request_evidence";
  }
}
