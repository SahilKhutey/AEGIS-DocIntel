# 15 — Security and Data Integrity

## 1. Zero Metric Fabrication Mandate
A core architectural principle of AEGIS-DocIntel is sovereign auditability: the frontend visualizes verified system data. It must never manufacture telemetry or coerce missing measurements into misleading zeros.

- `formatMetricValue(value)` returns explicit `"N/A"` or custom fallback string when values are `null`, `undefined`, or `NaN`.
- `calculatePercentageChange(current, previous)` returns `null` when baselines are absent, preventing synthetic +100% or 0% trends.

## 2. OWASP Formula Injection Neutralization
To protect users exporting document analytics to spreadsheet environments (Excel, Sheets, Calc), `toCsv()` neutralizes formula injection vectors:
- Dangerous prefix characters: `=`, `+`, `-`, `@`, `\t`, `\r`
- Neutralization mechanism: Prepends a single quote (`'`), which spreadsheets interpret as an instruction to treat the cell value strictly as text.
- Quote escaping: Inner quotes are doubled (`""`) and values containing delimiters are wrapped in standard RFC 4180 quotes.

## 3. Webhook SSRF Defense-in-Depth
Outbound webhook registration in `WebhookManager.tsx` enforces `isSafeWebhookUrl()`:
- Rejects non-HTTP(S) schemas
- Rejects loopback hostnames (`localhost`, `127.0.0.1`, `0.0.0.0`, `::1`)
- Rejects RFC1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
- Rejects cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`)

## 4. API Credential Safety
- API secrets (`aegis_live_sec_...`) are only returned once upon generation and held in transient component state.
- They are never written to `localStorage`, `sessionStorage`, or telemetry logs.
- Key listings display only the non-sensitive prefix (`aegis_live_****3fa9`).
