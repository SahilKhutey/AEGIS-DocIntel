import { describe, expect, it } from "vitest";
import {
  NAVIGATION,
  isNavigationItemActive,
  getActiveNavigationItem,
} from "@/config/navigation";
import { getVisibleNavigation } from "@/features/access/navigation-access";

describe("AEGIS navigation", () => {
  it("contains unique navigation group identifiers", () => {
    const ids = NAVIGATION.map((group) => group.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("contains unique item identifiers", () => {
    const ids = NAVIGATION.flatMap((group) =>
      group.items.map((item) => item.id),
    );
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("contains unique navigation paths", () => {
    const paths = NAVIGATION.flatMap((group) =>
      group.items.map((item) => item.href),
    );
    expect(new Set(paths).size).toBe(paths.length);
  });

  it("marks document library active on its route", () => {
    const item = NAVIGATION
      .flatMap((group) => group.items)
      .find((entry) => entry.href === "/documents");

    expect(item).toBeDefined();
    expect(isNavigationItemActive("/documents", item!)).toBe(true);
  });

  it("keeps parent navigation active on nested routes", () => {
    const item = NAVIGATION
      .flatMap((group) => group.items)
      .find((entry) => entry.href === "/documents");

    expect(item).toBeDefined();
    expect(
      isNavigationItemActive("/documents/doc-123", item!),
    ).toBe(true);
  });

  it("does not match unrelated route prefixes", () => {
    const item = NAVIGATION
      .flatMap((group) => group.items)
      .find((entry) => entry.href === "/documents");

    expect(item).toBeDefined();
    expect(
      isNavigationItemActive("/documents-old", item!),
    ).toBe(false);
  });

  it("hides planned features", () => {
    const visible = getVisibleNavigation([
      "workspace.read",
      "documents.read",
      "documents.upload",
      "intelligence.query",
      "documents.compare",
      "evidence.read",
      "governance.read",
      "governance.review",
    ]);

    const ids = visible.flatMap((group) =>
      group.items.map((item) => item.id),
    );

    expect(ids).not.toContain("processing");
    expect(ids).not.toContain("analytics");
    expect(ids).not.toContain("settings");
  });

  it("does not expose routes without permission", () => {
    const visible = getVisibleNavigation([
      "workspace.read",
      "documents.read",
    ]);

    const ids = visible.flatMap((group) =>
      group.items.map((item) => item.id),
    );

    expect(ids).toContain("overview");
    expect(ids).toContain("document-library");
    expect(ids).not.toContain("reviews");
  });

  it("resolves the active page", () => {
    expect(getActiveNavigationItem("/ask")?.label).toBe("Ask AEGIS");
    expect(getActiveNavigationItem("/reviews/123")?.label).toBe(
      "Review Queue",
    );
  });

  it("does not return an active item for an unknown route", () => {
    expect(getActiveNavigationItem("/unknown")).toBeUndefined();
  });
});
