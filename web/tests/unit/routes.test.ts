import { describe, expect, it } from "vitest";
import { ROUTES } from "@/config/routes";
import { matchesRoute } from "@/lib/route-matching";

describe("AEGIS route architecture", () => {
  it("contains unique route identifiers", () => {
    const ids = ROUTES.map((route) => route.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("contains unique route patterns", () => {
    const paths = ROUTES.map((route) => route.path);
    expect(new Set(paths).size).toBe(paths.length);
  });

  it("matches the document library route", () => {
    const route = ROUTES.find((r) => r.id === "documents")!;
    expect(matchesRoute("/documents", route)).toBe(true);
  });

  it("matches a document detail route", () => {
    const route = ROUTES.find(
      (r) => r.id === "document-detail",
    )!;
    expect(
      matchesRoute("/documents/document-123", route),
    ).toBe(true);
  });

  it("does not match an incomplete document detail route", () => {
    const route = ROUTES.find(
      (r) => r.id === "document-detail",
    )!;
    expect(matchesRoute("/documents/", route)).toBe(false);
  });

  it("does not match unrelated paths", () => {
    const route = ROUTES.find((r) => r.id === "documents")!;
    expect(matchesRoute("/documents-old", route)).toBe(false);
  });

  it("marks unimplemented routes as planned", () => {
    expect(
      ROUTES.find((r) => r.id === "evidence")?.status,
    ).toBe("planned");
  });
});
