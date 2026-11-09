import { describe, it, expect } from "vitest";
import { toCsv, sanitizeCsvCell } from "@/lib/advanced/export-data";

describe("export-data utility & formula injection prevention", () => {
  it("sanitizes regular values", () => {
    expect(sanitizeCsvCell("hello")).toBe("hello");
    expect(sanitizeCsvCell(123)).toBe("123");
    expect(sanitizeCsvCell(null)).toBe("");
    expect(sanitizeCsvCell(undefined)).toBe("");
  });

  it("escapes formula injection prefixes with leading single quote", () => {
    // OWASP formula injection prefixes: =, +, -, @, \t, \r
    expect(sanitizeCsvCell("=SUM(A1:B1)")).toBe(`"'=SUM(A1:B1)"`);
    expect(sanitizeCsvCell("+cmd|' /C calc'!A0")).toBe(`"'+cmd|' /C calc'!A0"`);
    expect(sanitizeCsvCell("-1+1")).toBe(`"'-1+1"`);
    expect(sanitizeCsvCell("@malicious")).toBe(`"'@malicious"`);
    expect(sanitizeCsvCell("\tcalc")).toBe(`"'\tcalc"`);
  });

  it("escapes internal quotes and commas properly", () => {
    expect(sanitizeCsvCell('He said "hello"')).toBe('"He said ""hello"""');
    expect(sanitizeCsvCell("a, b, c")).toBe('"a, b, c"');
  });

  it("converts rows to CSV with headers", () => {
    const rows = [
      { id: "doc-1", name: "Report", count: 10 },
      { id: "doc-2", name: "Summary, Q3", count: 25 },
    ];
    const csv = toCsv(rows);
    const lines = csv.split("\r\n");
    expect(lines[0]).toBe("id,name,count");
    expect(lines[1]).toBe("doc-1,Report,10");
    expect(lines[2]).toBe('doc-2,"Summary, Q3",25');
  });

  it("respects custom column mappings", () => {
    const rows = [{ id: "doc-1", name: "Doc A", secret: "hidden" }];
    const cols = [
      { key: "id", label: "Identifier" },
      { key: "name", label: "Document Name" },
    ];
    const csv = toCsv(rows, cols);
    expect(csv).toContain("Identifier,Document Name");
    expect(csv).not.toContain("hidden");
  });

  it("handles empty rows array", () => {
    expect(toCsv([])).toBe("");
    const cols = [{ key: "col1", label: "Column 1" }];
    expect(toCsv([], cols)).toBe("Column 1");
  });
});
