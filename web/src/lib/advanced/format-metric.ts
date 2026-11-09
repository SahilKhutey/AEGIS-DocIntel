export type MetricFormat =
  | "number"
  | "currency"
  | "percent"
  | "duration"
  | "bytes";

export interface FormatMetricOptions {
  decimals?: number;
  currencySymbol?: string;
  fallback?: string;
}

/**
 * Formats a raw metric value safely.
 * Crucial rule: Does NOT coerce null or undefined to 0. Returns "N/A" or options.fallback.
 */
export function formatMetricValue(
  value: number | null | undefined,
  format: MetricFormat = "number",
  options: FormatMetricOptions = {},
): string {
  const fallback = options.fallback ?? "N/A";

  if (value === null || value === undefined || Number.isNaN(value)) {
    return fallback;
  }

  const decimals = options.decimals ?? (format === "percent" || format === "currency" ? 2 : 0);

  switch (format) {
    case "currency": {
      const symbol = options.currencySymbol ?? "$";
      return `${symbol}${value.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}`;
    }
    case "percent": {
      // If value is between 0 and 1, we could multiply by 100, but if it's already 0-100, check convention:
      // In AEGIS contracts: rates like approval_rate are between 0 and 100 or 0 and 1.
      // If <= 1.0, we treat as fraction 0-100%, else treat as already percentage.
      const pct = value <= 1.0 && value >= 0 && decimals > 0 ? value * 100 : value;
      return `${pct.toFixed(decimals)}%`;
    }
    case "duration": {
      // Assuming milliseconds
      if (value < 1000) {
        return `${Math.round(value)}ms`;
      }
      const seconds = value / 1000;
      if (seconds < 60) {
        return `${seconds.toFixed(1)}s`;
      }
      const minutes = Math.floor(seconds / 60);
      const remainingSecs = Math.round(seconds % 60);
      return `${minutes}m ${remainingSecs}s`;
    }
    case "bytes": {
      if (value < 1024) return `${value} B`;
      const kb = value / 1024;
      if (kb < 1024) return `${kb.toFixed(1)} KB`;
      const mb = kb / 1024;
      if (mb < 1024) return `${mb.toFixed(1)} MB`;
      const gb = mb / 1024;
      return `${gb.toFixed(2)} GB`;
    }
    case "number":
    default: {
      return value.toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
    }
  }
}

export interface MetricChange {
  changePercent: number;
  direction: "increase" | "decrease" | "neutral";
  formattedText: string;
}

/**
 * Calculates percentage change between current and previous values.
 * Returns null if either value is null/undefined.
 */
export function calculatePercentageChange(
  current: number | null | undefined,
  previous: number | null | undefined,
): MetricChange | null {
  if (
    current === null ||
    current === undefined ||
    previous === null ||
    previous === undefined ||
    Number.isNaN(current) ||
    Number.isNaN(previous)
  ) {
    return null;
  }

  if (previous === 0) {
    if (current === 0) {
      return { changePercent: 0, direction: "neutral", formattedText: "0.0%" };
    }
    return {
      changePercent: 100,
      direction: current > 0 ? "increase" : "decrease",
      formattedText: current > 0 ? "+100%" : "-100%",
    };
  }

  const rawChange = ((current - previous) / Math.abs(previous)) * 100;
  const changePercent = Math.abs(rawChange);

  let direction: "increase" | "decrease" | "neutral" = "neutral";
  if (rawChange > 0.05) {
    direction = "increase";
  } else if (rawChange < -0.05) {
    direction = "decrease";
  }

  const sign = rawChange > 0 ? "+" : rawChange < 0 ? "-" : "";
  const formattedText = `${sign}${changePercent.toFixed(1)}%`;

  return {
    changePercent,
    direction,
    formattedText,
  };
}
