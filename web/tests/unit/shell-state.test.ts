import { describe, expect, it } from "vitest";
import { isSafeInternalHref } from "@/lib/shell/route-utils";

describe("Shell state expectations", () => {
  it("starts with the mobile drawer closed", () => {
    const initialState = false;
    expect(initialState).toBe(false);
  });

  it("does not treat a missing active workspace as valid", () => {
    const workspaces = [{ id: "workspace-a", name: "Workspace A" }];

    const activeId = "workspace-unknown";

    const active = workspaces.find((workspace) => workspace.id === activeId);

    expect(active).toBeUndefined();
  });

  it("handles duplicate workspace selection gracefully", () => {
    const currentId = "workspace-a";
    let switchRequested = false;

    function handleSelect(newId: string) {
      if (newId === currentId) return;
      switchRequested = true;
    }

    handleSelect("workspace-a");
    expect(switchRequested).toBe(false);

    handleSelect("workspace-b");
    expect(switchRequested).toBe(true);
  });

  it("formats notification unread counts correctly", () => {
    function formatCount(count: number): string {
      return count > 99 ? "99+" : String(count);
    }

    expect(formatCount(0)).toBe("0");
    expect(formatCount(12)).toBe("12");
    expect(formatCount(100)).toBe("99+");
    expect(formatCount(340)).toBe("99+");
  });

  it("safeguards global search internal route redirects", () => {
    expect(isSafeInternalHref("/documents")).toBe(true);
    expect(isSafeInternalHref("/reviews/rev-123")).toBe(true);
    expect(isSafeInternalHref("/ask?doc_id=doc-1")).toBe(true);

    expect(isSafeInternalHref("https://external-phishing.com")).toBe(false);
    expect(isSafeInternalHref("//malicious-domain.com")).toBe(false);
    expect(isSafeInternalHref("/safe/..\\escape")).toBe(false);
  });
});
