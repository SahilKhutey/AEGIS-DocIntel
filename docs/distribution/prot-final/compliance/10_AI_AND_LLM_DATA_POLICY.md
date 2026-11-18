# AI & External Model Provider Policy (POL-011)

## Safeguards for External Model Usage
- **Server-Side Routing:** Model provider credentials never distributed to client artifacts.
- **Data Minimization:** Only relevant document snippets matching user queries are forwarded to LLMs.
- **Zero Model Training:** Explicit contractual exclusion of customer evaluation data from public model training.
- **Fail-Closed Redaction:** Provider errors and tracebacks redacted before returning to evaluators.
