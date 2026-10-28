import { describe, expect, it } from "vitest";
import { DecisionInputSchema } from "./submit-decision";

describe("DecisionInputSchema", () => {
  it("accepts valid approve input", () => {
    const valid = {
      action: "approve",
      expected_version: 1,
      rationale: "Approved after verifying quote against section 4",
    };
    const parsed = DecisionInputSchema.parse(valid);
    expect(parsed.action).toBe("approve");
    expect(parsed.expected_version).toBe(1);
  });

  it("rejects rationale shorter than 3 characters", () => {
    const invalid = {
      action: "approve",
      expected_version: 1,
      rationale: "ok",
    };
    expect(() => DecisionInputSchema.parse(invalid)).toThrow();
  });

  it("accepts valid correct input with corrected_value", () => {
    const valid = {
      action: "correct",
      expected_version: 2,
      rationale: "Corrected amount per amendment A",
      corrected_value: 5000000,
      corrected_type: "decimal",
      unit: "USD",
      evidence_quote: "The revised cap is $5,000,000 USD",
    };
    const parsed = DecisionInputSchema.parse(valid);
    expect(parsed.action).toBe("correct");
    expect(parsed.corrected_value).toBe(5000000);
  });
});
