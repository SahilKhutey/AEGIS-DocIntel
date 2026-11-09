export type TimeRangePreset = "24h" | "7d" | "30d" | "90d" | "all" | "custom";

export interface TimeRangeOption {
  value: TimeRangePreset;
  label: string;
}

export const TIME_RANGE_OPTIONS: TimeRangeOption[] = [
  { value: "24h", label: "Last 24 Hours" },
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
  { value: "90d", label: "Last 90 Days" },
  { value: "all", label: "All Time" },
  { value: "custom", label: "Custom Range" },
];

export interface ResolvedTimeRange {
  startDate: string;
  endDate: string;
  label: string;
}

/**
 * Calculates start and end ISO dates for a given preset.
 * Reference date defaults to now if not provided (useful for deterministic tests).
 */
export function getTimeRangeDates(
  range: TimeRangePreset,
  customStart?: string,
  customEnd?: string,
  referenceDate: Date = new Date(),
): ResolvedTimeRange {
  const endDate = referenceDate.toISOString();
  const refMs = referenceDate.getTime();

  switch (range) {
    case "24h": {
      const start = new Date(refMs - 24 * 60 * 60 * 1000);
      return {
        startDate: start.toISOString(),
        endDate,
        label: "Last 24 Hours",
      };
    }
    case "7d": {
      const start = new Date(refMs - 7 * 24 * 60 * 60 * 1000);
      return {
        startDate: start.toISOString(),
        endDate,
        label: "Last 7 Days",
      };
    }
    case "30d": {
      const start = new Date(refMs - 30 * 24 * 60 * 60 * 1000);
      return {
        startDate: start.toISOString(),
        endDate,
        label: "Last 30 Days",
      };
    }
    case "90d": {
      const start = new Date(refMs - 90 * 24 * 60 * 60 * 1000);
      return {
        startDate: start.toISOString(),
        endDate,
        label: "Last 90 Days",
      };
    }
    case "custom": {
      return {
        startDate: customStart || new Date(refMs - 7 * 24 * 60 * 60 * 1000).toISOString(),
        endDate: customEnd || endDate,
        label: "Custom Range",
      };
    }
    case "all":
    default: {
      return {
        startDate: new Date(0).toISOString(),
        endDate,
        label: "All Time",
      };
    }
  }
}
