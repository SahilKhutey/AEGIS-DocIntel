import { describe, expect, it } from "vitest";
import { getBreadcrumbs } from "@/lib/shell/breadcrumbs";

describe("getBreadcrumbs", () => {
  it("returns overview breadcrumbs", () => {
    expect(getBreadcrumbs("/").map((item) => item.label)).toEqual([
      "Workspace",
      "Overview",
    ]);
  });

  it("returns document list breadcrumbs", () => {
    expect(getBreadcrumbs("/documents").map((item) => item.label)).toEqual([
      "Workspace",
      "Documents",
    ]);
  });

  it("returns document detail breadcrumbs", () => {
    expect(
      getBreadcrumbs("/documents/doc-123").map((item) => item.label)
    ).toEqual(["Workspace", "Documents", "Document details"]);
  });

  it("returns review detail breadcrumbs", () => {
    expect(
      getBreadcrumbs("/reviews/review-123").map((item) => item.label)
    ).toEqual(["Workspace", "Reviews", "Review details"]);
  });
});
