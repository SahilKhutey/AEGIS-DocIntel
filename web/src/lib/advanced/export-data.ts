/**
 * OWASP Formula Injection Neutralization:
 * Spreadsheet applications (Excel, Calc, Google Sheets) interpret cells starting
 * with =, +, -, @, \t, or \r as formulas, which can trigger command execution or data exfiltration.
 * We neutralize dangerous leading characters by prefixing a single quote (').
 */
export function sanitizeCsvCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  const str = String(value);

  // Check if dangerous leading characters exist
  const dangerousPrefixes = ["=", "+", "-", "@", "\t", "\r"];
  let sanitized = str;

  if (dangerousPrefixes.some((prefix) => str.startsWith(prefix))) {
    sanitized = `'${str}`;
  }

  // Escape inner double quotes by doubling them: " -> ""
  const escaped = sanitized.replace(/"/g, '""');

  // Wrap in quotes if it contains commas, newlines, or quotes
  if (escaped.includes(",") || escaped.includes("\n") || escaped.includes("\r") || escaped.includes('"') || sanitized.startsWith("'")) {
    return `"${escaped}"`;
  }

  return escaped;
}

export interface CsvColumn<T = Record<string, unknown>> {
  key: keyof T | string;
  label: string;
}

/**
 * Converts an array of objects to a safe CSV formatted string.
 */
export function toCsv<T extends Record<string, unknown>>(
  rows: T[],
  columns?: CsvColumn<T>[],
): string {
  if (!rows || rows.length === 0) {
    if (columns && columns.length > 0) {
      return columns.map((c) => sanitizeCsvCell(c.label)).join(",");
    }
    return "";
  }

  // Derive columns if not provided
  const cols =
    columns ||
    Object.keys(rows[0]).map((key) => ({
      key,
      label: key,
    }));

  // Header row
  const header = cols.map((col) => sanitizeCsvCell(col.label)).join(",");

  // Data rows
  const dataRows = rows.map((row) =>
    cols
      .map((col) => {
        const val = row[col.key as keyof T];
        return sanitizeCsvCell(val);
      })
      .join(","),
  );

  return [header, ...dataRows].join("\r\n");
}

/**
 * Triggers client-side download of generated CSV content.
 */
export function downloadCsv(filename: string, csvContent: string): void {
  if (typeof window === "undefined") return;

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", filename.endsWith(".csv") ? filename : `${filename}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
