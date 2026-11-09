import { describe, expect, it } from "vitest";

import {
  NAVIGATION,
  getActiveNavigationItem,
  isNavigationItemActive,
} from "../../src/config/navigation";

describe("AEGIS navigation architecture", () => {
  it("contains unique navigation group identifiers", () => {
    const ids = NAVIGATION.map((group) => group.id);

    expect(new Set(ids).size).toBe(ids.length);
  });

  it("contains unique navigation hrefs", () => {
    const hrefs = NAVIGATION.flatMap((group) =>
      group.items.map((item) => item.href),
    );

    expect(new Set(hrefs).size).toBe(hrefs.length);
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

  it("does not activate planned navigation items", () => {
    const item = NAVIGATION
      .flatMap((group) => group.items)
      .find((entry) => entry.href === "/processing");

    expect(item).toBeDefined();
    expect(
      isNavigationItemActive("/processing", item!),
    ).toBe(false);
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
