---
name: Pilot feedback
about: Structured feedback from pilot program participants
title: "[PILOT] "
labels: ["pilot-feedback"]
---

**What were you trying to accomplish?**
Describe your document processing, RAG, or context extraction objective (e.g., extracting multi-column tables, scrubbing PII from customer transcripts, packing documents under fixed token budgets).

**Which component did you use?**
- [ ] `aegis-docprep` standalone package (PII redaction / context packing / reading order)
- [ ] Full platform (ingestion + math engines + REST API query)
- [ ] Client SDK (Python / TypeScript / Java / C++)

**Input Document Profile**
- Document format: [PDF, DOCX, XLSX, PPTX, Plain text, Scanned image]
- Page count / size: [e.g. 15 pages, 2.4 MB]
- Layout complexity: [Single column, Multi-column, Tables/Spreadsheet, Mixed form]

**Accuracy & Correctness**
Did the output match what you expected from the real document content?
- [ ] Yes, output was accurate and matched expectations.
- [ ] Partially, output had minor discrepancies (explain below).
- [ ] No, output was inaccurate or degraded (explain below).

*Details on output quality:*

**What broke, if anything?**
List any unexpected exceptions, unhandled document structures, slow performance, or installation friction.

**Token / Latency Metrics (if measured)**
- Input raw token count:
- Output context token count / reduction %:
- Processing latency (seconds/ms):

**Would you use this again? Why or why not?**
Provide your honest assessment on whether this primitive/pipeline is viable for your workflow.
