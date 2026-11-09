import { describe, it, expect } from "vitest";
import {
  isTerminalStatus,
  getProposedAllowedDecisions,
  canExecuteAction,
  getTransitionTargetStatus,
} from "@/features/governance/utils/decision-transitions";

describe("decision-transitions utility", () => {
  it("correctly identifies terminal vs non-terminal review states", () => {
    expect(isTerminalStatus("approved")).toBe(true);
    expect(isTerminalStatus("corrected")).toBe(true);
    expect(isTerminalStatus("rejected")).toBe(true);

    expect(isTerminalStatus("pending")).toBe(false);
    expect(isTerminalStatus("in_review")).toBe(false);
    expect(isTerminalStatus("needs_evidence")).toBe(false);
  });

  it("returns allowed transitions for each review status", () => {
    expect(getProposedAllowedDecisions("pending")).toEqual(["claim"]);
    expect(getProposedAllowedDecisions("needs_evidence")).toEqual(["claim"]);
    expect(getProposedAllowedDecisions("in_review")).toEqual([
      "approve",
      "correct",
      "reject",
      "request_evidence",
    ]);
    expect(getProposedAllowedDecisions("approved")).toEqual(["reopen"]);
    expect(getProposedAllowedDecisions("corrected")).toEqual(["reopen"]);
    expect(getProposedAllowedDecisions("rejected")).toEqual(["reopen"]);
  });

  it("checks canExecuteAction correctly", () => {
    expect(canExecuteAction("in_review", "approve")).toBe(true);
    expect(canExecuteAction("in_review", "correct")).toBe(true);
    expect(canExecuteAction("in_review", "claim")).toBe(false);
    expect(canExecuteAction("pending", "claim")).toBe(true);
    expect(canExecuteAction("pending", "approve")).toBe(false);
    expect(canExecuteAction("approved", "reopen")).toBe(true);
    expect(canExecuteAction("approved", "reject")).toBe(false);
  });

  it("maps action to expected target state", () => {
    expect(getTransitionTargetStatus("claim")).toBe("in_review");
    expect(getTransitionTargetStatus("approve")).toBe("approved");
    expect(getTransitionTargetStatus("correct")).toBe("corrected");
    expect(getTransitionTargetStatus("reject")).toBe("rejected");
    expect(getTransitionTargetStatus("request_evidence")).toBe("needs_evidence");
    expect(getTransitionTargetStatus("reopen")).toBe("in_review");
    expect(getTransitionTargetStatus("create")).toBe("pending");
  });
});
