import { describe, expect, it } from "vitest";
import { WORKFLOWS } from "@/config/workflows";

describe("AEGIS workflow architecture", () => {
  it("has unique workflow identifiers", () => {
    const ids = WORKFLOWS.map((workflow) => workflow.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("has unique step identifiers within each workflow", () => {
    for (const workflow of WORKFLOWS) {
      const ids = workflow.steps.map((step) => step.id);
      expect(new Set(ids).size).toBe(ids.length);
    }
  });

  it("defines a failure state for every workflow", () => {
    for (const workflow of WORKFLOWS) {
      expect(workflow.failureStates.length).toBeGreaterThan(0);
    }
  });

  it("defines document ingestion", () => {
    const workflow = WORKFLOWS.find(
      (item) => item.id === "document-ingestion",
    );
    expect(workflow).toBeDefined();
    expect(workflow?.entryRoute).toBe("/documents");
  });

  it("defines intelligence query", () => {
    const workflow = WORKFLOWS.find(
      (item) => item.id === "intelligence-query",
    );
    expect(workflow?.entryRoute).toBe("/ask");
  });

  it("defines governance review", () => {
    const workflow = WORKFLOWS.find(
      (item) => item.id === "governance-review",
    );
    expect(workflow?.requiredPermissions).toContain(
      "governance.review",
    );
  });
});
