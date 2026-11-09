import { describe, it, expect } from "vitest";
import { getTimeRangeDates, TIME_RANGE_OPTIONS } from "@/lib/advanced/time-range";

describe("time-range utility", () => {
  const fixedDate = new Date("2026-11-09T12:00:00.000Z");

  it("exports valid time range options", () => {
    expect(TIME_RANGE_OPTIONS.length).toBeGreaterThan(0);
    expect(TIME_RANGE_OPTIONS.find((opt) => opt.value === "24h")).toBeDefined();
    expect(TIME_RANGE_OPTIONS.find((opt) => opt.value === "7d")).toBeDefined();
  });

  it("calculates 24h range correctly", () => {
    const range = getTimeRangeDates("24h", undefined, undefined, fixedDate);
    expect(range.label).toBe("Last 24 Hours");
    expect(range.endDate).toBe(fixedDate.toISOString());
    const expectedStart = new Date(fixedDate.getTime() - 24 * 60 * 60 * 1000).toISOString();
    expect(range.startDate).toBe(expectedStart);
  });

  it("calculates 7d range correctly", () => {
    const range = getTimeRangeDates("7d", undefined, undefined, fixedDate);
    expect(range.label).toBe("Last 7 Days");
    const expectedStart = new Date(fixedDate.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString();
    expect(range.startDate).toBe(expectedStart);
  });

  it("calculates custom range when provided", () => {
    const customStart = "2026-10-01T00:00:00.000Z";
    const customEnd = "2026-10-15T23:59:59.000Z";
    const range = getTimeRangeDates("custom", customStart, customEnd, fixedDate);
    expect(range.label).toBe("Custom Range");
    expect(range.startDate).toBe(customStart);
    expect(range.endDate).toBe(customEnd);
  });

  it("handles all-time range", () => {
    const range = getTimeRangeDates("all", undefined, undefined, fixedDate);
    expect(range.label).toBe("All Time");
    expect(range.startDate).toBe(new Date(0).toISOString());
    expect(range.endDate).toBe(fixedDate.toISOString());
  });
});
