# 02 — Analytics and Reporting Specification

## 1. Functional Scope
The Analytics Workspace (`/analytics`) surfaces telemetry across document ingestion, embedding density, query latency, LLM token expenditure, and human review throughput.

## 2. Telemetry Contracts
Data is derived from three primary backend contracts:
1. `GET /v1/admin/stats?range={range}`:
   - `doc_count`: Total active ingested documents
   - `chunk_count`: Total segmented vector chunks
   - `total_tokens_used`: Cumulative prompt and completion tokens
   - `total_cost_usd`: Estimated cumulative inference expenditure
   - `cache_hit_rate`: Percent of queries answered via vector caching
   - `avg_query_latency_ms`: Mean end-to-end question answering duration
2. `GET /v1/admin/token-usage?range={range}`:
   - Token breakdown into prompt context tokens vs completion tokens
   - Model-level distribution (`text-embedding-3-small`, `gemini-1.5-pro`, `gpt-4o-mini`)
3. `GET /v1/reviews/metrics?range={range}`:
   - `total_items`: Total candidate facts evaluated
   - `approval_rate`: Ratio of approved facts without edits
   - `correction_rate`: Ratio of facts amended prior to approval
   - `rejection_rate`: Ratio of candidate facts marked invalid

## 3. OWASP Formula Injection Neutralization
Exported data downloaded via CSV is sanitized using `toCsv()` in `web/src/lib/advanced/export-data.ts`.
Spreadsheet software (Microsoft Excel, LibreOffice Calc, Google Sheets) interprets leading characters `=`, `+`, `-`, `@`, `\t`, `\r` as executable formulas.
All cell values beginning with these prefixes are neutralized with a leading single quote (`'`), ensuring client environments interpret values exclusively as plaintext.
