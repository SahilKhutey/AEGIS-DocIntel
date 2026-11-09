import { describe, it, expect } from "vitest";
import {
  formatMetricValue,
  calculatePercentageChange,
} from "@/lib/advanced/format-metric";

describe("format-metric utility", () => {
  it("never coerces null or undefined to 0", () => {
    expect(formatMetricValue(null, "number")).toBe("N/A");
    expect(formatMetricValue(undefined, "currency")).toBe("N/A");
    expect(formatMetricValue(Number.NaN, "percent")).toBe("N/A");
    expect(formatMetricValue(null, "number", { fallback: "--" })).toBe("--");
  });

  it("formats numbers properly", () => {
    expect(formatMetricValue(1234, "number")).toBe("1,234");
    expect(formatMetricValue(1234.567, "number", { decimals: 2 })).toBe("1,234.57");
  });

  it("formats currencies properly", () => {
    expect(formatMetricValue(45.2, "currency")).toBe("$45.20");
    expect(formatMetricValue(1000, "currency", { currencySymbol: "€" })).toBe("€1,000.00");
  });

  it("formats percentages properly", () => {
    // 0.85 as a fraction
    expect(formatMetricValue(0.85, "percent")).toBe("85.00%");
    // Already scaled percentage
    expect(formatMetricValue(92.5, "percent", { decimals: 1 })).toBe("92.5%");
  });

  it("formats durations properly", () => {
    expect(formatMetricValue(450, "duration")).toBe("450ms");
    expect(formatMetricValue(1500, "duration")).toBe("1.5s");
    expect(formatMetricValue(75000, "duration")).toBe("1m 15s");
  });

  it("formats bytes properly", () => {
    expect(formatMetricValue(500, "bytes")).toBe("500 B");
    expect(formatMetricValue(2048, "bytes")).toBe("2.0 KB");
    expect(formatMetricValue(1048576 * 5, "bytes")).toBe("5.0 MB");
  });

  describe("calculatePercentageChange", () => {
    it("returns null when current or previous is missing", () => {
      expect(calculatePercentageChange(null, 10)).toBeNull();
      expect(calculatePercentageChange(10, undefined)).toBeNull();
    });

    it("calculates increase correctly", () => {
      const res = calculatePercentageChange(120, 100);
      expect(res).not.toBeNull();
      expect(res?.direction).toBe("increase");
      expect(res?.changePercent).toBeCloseTo(20);
      expect(res?.formattedText).toBe("+20.0%");
    });

    it("calculates decrease correctly", () => {
      const res = calculatePercentageChange(80, 100);
      expect(res).not.toBeNull();
      expect(res?.direction).toBe("decrease");
      expect(res?.changePercent).toBeCloseTo(20);
      expect(res?.formattedText).toBe("-20.0%");
    });

    it("handles zero baseline gracefully", () => {
      const res = calculatePercentageChange(10, 0);
      expect(res?.direction).toBe("increase");
      expect(res?.formattedText).toBe("+100%");

      const zeroZero = calculatePercentageChange(0, 0);
      expect(zeroZero?.direction).toBe("neutral");
      expect(zeroZero?.formattedText).toBe("0.0%");
    });
  });
});
