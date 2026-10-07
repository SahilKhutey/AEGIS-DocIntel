# Benchmark Dataset Provenance & Licensing

## Overview
This benchmark corpus (`production/benchmark-dataset-real/pdf-corpus/`) replaces the fabricated synthetic PDFs previously quarantined in `_unverified_archive/benchmark-dataset-mock/`.

## Sources

### 1. `jsvine/pdfplumber` Test Suite (62 PDFs)
- **Repository:** https://github.com/jsvine/pdfplumber (`tests/pdfs`)
- **License:** MIT License (see `production/benchmark-dataset-real/LICENSE.txt`)
- **Profile:** Real-world PDFs collected over 10+ years specifically because they represent challenging edge cases:
  - `federal-register-2020-17221.pdf` — Real 15-page U.S. Federal Register notice (multi-column, footnotes, table)
  - `table-curves-example.pdf` — Complex curve-bounded tabular document
  - `chelsea_pdta.pdf` — Public municipal document with extensive tables (92 tables detected)
  - `WARN-Report-for-7-1-2015-to-03-25-2016.pdf` — Government labor filing with tabular records
  - `password-example.pdf` — Real encrypted, password-protected PDF fixture
  - `empty.pdf` — Zero-length document edge case
  - `annotations-rotated-*.pdf` — Rotation and annotation object edge cases
  - Multiple real GitHub issue reproduction cases (`issue-*.pdf`, `pr-*.pdf`)

### 2. Native Research Paper
- `real_research_paper.pdf` — 14-page AMDI-DocIntel research paper fixture (1.35 MB, 34,671 characters).

## Reproducibility
To execute the benchmark against this corpus:
```bash
python scripts/run_benchmark.py --corpus production/benchmark-dataset-real/pdf-corpus
```
