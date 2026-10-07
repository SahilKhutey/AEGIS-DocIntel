"""
AEGIS-DocIntel — Real Benchmark Evaluation Harness
====================================================
Runs every file in production/benchmark-dataset-real/{pdf-corpus,docx-corpus}
through the appropriate loader and records timing, throughput, and error
information to a CSV.

Usage:
    python scripts/run_benchmark.py

Output:
    production/benchmark-dataset-real/timing_results.csv

The CSV format is:
    file,format,size_bytes,pages,elapsed_ms,chars,words,status,error
"""
from __future__ import annotations

import asyncio
import csv
import sys
import time
import traceback
from pathlib import Path

# Ensure src/ is importable when run from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.pdf_loader import PDFLoader
from src.ingestion.docx_loader import DOCXLoader

ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = ROOT / "production" / "benchmark-dataset-real"
PDF_CORPUS = CORPUS_ROOT / "pdf-corpus"
DOCX_CORPUS = CORPUS_ROOT / "docx-corpus"
OUTPUT_CSV = CORPUS_ROOT / "timing_results.csv"


async def _run_pdf(loader: PDFLoader, path: Path) -> dict:
    """Load one PDF and return a result row dict."""
    raw = path.read_bytes()
    size_bytes = len(raw)
    try:
        t0 = time.perf_counter()
        doc = await loader.load(raw, filename=path.name)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "file": path.name,
            "format": "pdf",
            "size_bytes": size_bytes,
            "pages": doc.page_count,
            "elapsed_ms": elapsed_ms,
            "chars": doc.char_count,
            "words": doc.word_count,
            "status": "ok",
            "error": "",
        }
    except Exception as exc:
        return {
            "file": path.name,
            "format": "pdf",
            "size_bytes": size_bytes,
            "pages": 0,
            "elapsed_ms": 0,
            "chars": 0,
            "words": 0,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }


async def _run_docx(loader: DocxLoader, path: Path) -> dict:
    """Load one DOCX and return a result row dict."""
    raw = path.read_bytes()
    size_bytes = len(raw)
    try:
        t0 = time.perf_counter()
        doc = await loader.load(raw, filename=path.name)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return {
            "file": path.name,
            "format": "docx",
            "size_bytes": size_bytes,
            "pages": doc.page_count,
            "elapsed_ms": elapsed_ms,
            "chars": doc.char_count,
            "words": doc.word_count,
            "status": "ok",
            "error": "",
        }
    except Exception as exc:
        return {
            "file": path.name,
            "format": "docx",
            "size_bytes": size_bytes,
            "pages": 0,
            "elapsed_ms": 0,
            "chars": 0,
            "words": 0,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }


async def main() -> None:
    pdf_loader = PDFLoader()
    docx_loader = DOCXLoader()
    rows: list[dict] = []

    # PDF corpus
    pdf_files = sorted(PDF_CORPUS.glob("*.pdf")) if PDF_CORPUS.exists() else []
    print(f"Found {len(pdf_files)} PDF files in {PDF_CORPUS}")
    for i, path in enumerate(pdf_files, 1):
        print(f"  [{i}/{len(pdf_files)}] {path.name} ...", end="", flush=True)
        row = await _run_pdf(pdf_loader, path)
        rows.append(row)
        if row["status"] == "ok":
            print(f" {row['elapsed_ms']}ms, {row['chars']} chars, {row['pages']} pages")
        else:
            print(f" ERROR: {row['error'][:80]}")

    # DOCX corpus
    docx_files = sorted(DOCX_CORPUS.glob("*.docx")) if DOCX_CORPUS.exists() else []
    print(f"\nFound {len(docx_files)} DOCX files in {DOCX_CORPUS}")
    for i, path in enumerate(docx_files, 1):
        print(f"  [{i}/{len(docx_files)}] {path.name} ...", end="", flush=True)
        row = await _run_docx(docx_loader, path)
        rows.append(row)
        if row["status"] == "ok":
            print(f" {row['elapsed_ms']}ms, {row['chars']} chars")
        else:
            print(f" ERROR: {row['error'][:80]}")

    if not rows:
        print("\nNo corpus files found. Populate the corpus first.")
        return

    # Write CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["file", "format", "size_bytes", "pages", "elapsed_ms", "chars", "words", "status", "error"]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    ok_rows = [r for r in rows if r["status"] == "ok"]
    err_rows = [r for r in rows if r["status"] != "ok"]
    if ok_rows:
        elapsed_vals = [r["elapsed_ms"] for r in ok_rows]
        elapsed_vals_sorted = sorted(elapsed_vals)
        p95_idx = max(0, int(len(elapsed_vals_sorted) * 0.95) - 1)
        p95 = elapsed_vals_sorted[p95_idx]
        total_chars = sum(r["chars"] for r in ok_rows)
        total_bytes = sum(r["size_bytes"] for r in ok_rows)
        print(f"\n=== Benchmark Summary ===")
        print(f"Files processed:  {len(ok_rows)} ok / {len(err_rows)} errors")
        print(f"Total corpus:     {total_bytes / 1024 / 1024:.1f} MB")
        print(f"Total chars:      {total_chars:,}")
        print(f"Mean elapsed:     {sum(elapsed_vals) / len(elapsed_vals):.1f}ms")
        print(f"P95 elapsed:      {p95:.1f}ms")
        print(f"Max elapsed:      {max(elapsed_vals):.1f}ms")
        print(f"\nResults written to: {OUTPUT_CSV}")
    else:
        print("\nAll files errored — no summary statistics available.")

    if err_rows:
        print(f"\nErrors ({len(err_rows)} files):")
        for r in err_rows:
            print(f"  {r['file']}: {r['error']}")


if __name__ == "__main__":
    asyncio.run(main())
