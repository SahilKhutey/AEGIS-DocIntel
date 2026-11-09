import { describe, it, expect } from "vitest";
import {
  getStatusStyle,
  calculatePriority,
  PRIORITY_CONFIG,
} from "@/features/governance/utils/review-status";

describe("review-status utility", () => {
  it("provides config for all known statuses", () => {
    const statuses = [
      "pending",
      "in_review",
      "approved",
      "corrected",
      "rejected",
      "needs_evidence",
    ] as const;

    statuses.forEach((s) => {
      const style = getStatusStyle(s);
      expect(style.label).toBeDefined();
      expect(style.bg).toBeDefined();
      expect(style.text).toBeDefined();
      expect(style.border).toBeDefined();
    });
  });

  it("handles fallback for unknown statuses gracefully", () => {
    const fallback = getStatusStyle("custom_unknown_status");
    expect(fallback.label).toBe("custom unknown status");
    expect(fallback.bg).toBe("bg-gray-50");
  });

  it("calculates priority based on model confidence", () => {
    expect(calculatePriority(0.65)).toBe("high");
    expect(calculatePriority(0.85)).toBe("medium");
    expect(calculatePriority(0.98)).toBe("low");
    expect(calculatePriority(undefined)).toBe("medium");
  });

  it("provides valid priority styles", () => {
    expect(PRIORITY_CONFIG.high.text).toContain("rose");
    expect(PRIORITY_CONFIG.medium.text).toContain("amber");
    expect(PRIORITY_CONFIG.low.text).toContain("gray");
  });
});
