import { describe, it, expect } from "vitest";
import {
  hasDependencyCycle,
  topologicalSort,
} from "@/features/pipelines/utils/validate-graph";

describe("DAG cycle detection & topological sort", () => {
  it("detects no cycles in a linear DAG", () => {
    const nodes = ["A", "B", "C"];
    const edges = [
      { from: "A", to: "B" },
      { from: "B", to: "C" },
    ];
    expect(hasDependencyCycle(nodes, edges)).toBe(false);
    expect(topologicalSort(nodes, edges)).toEqual(["A", "B", "C"]);
  });

  it("detects no cycles in a branching DAG", () => {
    const nodes = ["ingest", "ocr", "layout", "embed", "index"];
    const edges = [
      { from: "ingest", to: "ocr" },
      { from: "ingest", to: "layout" },
      { from: "ocr", to: "embed" },
      { from: "layout", to: "embed" },
      { from: "embed", to: "index" },
    ];
    expect(hasDependencyCycle(nodes, edges)).toBe(false);
    const sorted = topologicalSort(nodes, edges);
    expect(sorted).not.toBeNull();
    expect(sorted?.indexOf("ingest")).toBe(0);
    expect(sorted?.indexOf("index")).toBe(4);
  });

  it("detects simple cycle (A -> B -> A)", () => {
    const nodes = ["A", "B"];
    const edges = [
      { from: "A", to: "B" },
      { from: "B", to: "A" },
    ];
    expect(hasDependencyCycle(nodes, edges)).toBe(true);
    expect(topologicalSort(nodes, edges)).toBeNull();
  });

  it("detects indirect cycle (A -> B -> C -> A)", () => {
    const nodes = ["A", "B", "C", "D"];
    const edges = [
      { from: "A", to: "B" },
      { from: "B", to: "C" },
      { from: "C", to: "A" },
      { from: "C", to: "D" },
    ];
    expect(hasDependencyCycle(nodes, edges)).toBe(true);
    expect(topologicalSort(nodes, edges)).toBeNull();
  });
});
