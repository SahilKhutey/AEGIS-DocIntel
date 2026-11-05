"""
aegis/audit/suites/processing.py
================================
Audit suite executing Document Processing and Extraction capability validations:
OCR, Layout Accuracy, Reading Order, Table Reconstruction, Normalization & Provenance
Invariants, Malformed Document Security, and Pipeline Performance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import jsonschema

from aegis.audit.suites.base import BaseAuditSuite


class ProcessingAuditSuite(BaseAuditSuite):
    suite_id = "processing"
    suite_name = "Document Processing and Extraction Audit Suite"
    suite_version = "1.0.0"
    description = (
        "Verifies OCR extraction, layout accuracy, reading order, table reconstruction, "
        "provenance invariants, sandbox security containment, and pipeline performance."
    )
    tags = ["processing", "ocr", "layout", "reading_order", "tables", "provenance", "security", "performance"]

    def validate(self, context: Any) -> None:
        """Verify presence of processing configurations and schemas."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        cfg_dir = root / "configs" / "processing"
        schema_dir = root / "schemas" / "processing"
        if not cfg_dir.exists():
            raise FileNotFoundError(f"Processing configuration directory not found at {cfg_dir}")
        if not schema_dir.exists():
            raise FileNotFoundError(f"Processing schema directory not found at {schema_dir}")

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute all processing capability audit checks."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        reports_dir = root / "artifacts" / "processing" / "reports"
        schema_dir = root / "schemas" / "processing"
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Load benchmark schema
        bench_schema_path = schema_dir / "benchmark.schema.json"
        bench_schema = {}
        if bench_schema_path.exists():
            with open(bench_schema_path, "r", encoding="utf-8") as f:
                bench_schema = json.load(f)

        # Check 1: OCR Extraction Benchmark
        try:
            ocr_path = reports_dir / "OCR_EXTRACTION_BENCHMARK.json"
            if not ocr_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-OCR-001",
                    "title": "OCR Extraction benchmark report missing",
                    "severity": "HIGH",
                    "description": f"Missing {ocr_path}",
                })
            else:
                with open(ocr_path, "r", encoding="utf-8") as f:
                    ocr_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(ocr_data, bench_schema)
                m = ocr_data.get("metrics", {})
                cer = m.get("native_pdf_cer", 1.0)
                acc = m.get("word_accuracy", 0.0)
                if cer <= 0.01 and acc >= 0.98:
                    passed += 1
                    artifacts.append({
                        "name": "ocr_extraction_benchmark",
                        "path": str(ocr_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-OCR-002",
                        "title": "OCR Extraction quality gate not met",
                        "severity": "HIGH",
                        "description": f"CER: {cer} (target <= 0.01), Word Accuracy: {acc} (target >= 0.98)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-OCR-003",
                "title": "OCR Extraction audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 2: Layout Accuracy Benchmark & Visual Overlays
        try:
            lay_path = reports_dir / "LAYOUT_ACCURACY_REPORT.json"
            svg_path = root / "artifacts" / "processing" / "visualizations" / "layout_sample_overlay.svg"
            if not lay_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-LAY-001",
                    "title": "Layout Accuracy report missing",
                    "severity": "HIGH",
                    "description": f"Missing {lay_path}",
                })
            else:
                with open(lay_path, "r", encoding="utf-8") as f:
                    lay_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(lay_data, bench_schema)
                m = lay_data.get("metrics", {})
                f1 = m.get("overall_f1", 0.0)
                map_score = m.get("mean_average_precision", 0.0)
                if f1 >= 0.85 and map_score >= 0.80 and svg_path.exists():
                    passed += 1
                    artifacts.append({
                        "name": "layout_accuracy_report",
                        "path": str(lay_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "layout_visual_overlay",
                        "path": str(svg_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-LAY-002",
                        "title": "Layout accuracy criteria or visualization missing",
                        "severity": "HIGH",
                        "description": f"F1: {f1} (target >= 0.85), mAP: {map_score} (target >= 0.80), SVG: {svg_path.exists()}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-LAY-003",
                "title": "Layout accuracy audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 3: Reading Order Benchmark
        try:
            ro_path = reports_dir / "READING_ORDER_REPORT.json"
            if not ro_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-ORD-001",
                    "title": "Reading order benchmark report missing",
                    "severity": "HIGH",
                    "description": f"Missing {ro_path}",
                })
            else:
                with open(ro_path, "r", encoding="utf-8") as f:
                    ro_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(ro_data, bench_schema)
                m = ro_data.get("metrics", {})
                tau = m.get("kendall_tau", 0.0)
                pair_acc = m.get("pairwise_ordering_accuracy", 0.0)
                if tau >= 0.90 and pair_acc >= 0.95:
                    passed += 1
                    artifacts.append({
                        "name": "reading_order_report",
                        "path": str(ro_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-ORD-002",
                        "title": "Reading order metrics below acceptable thresholds",
                        "severity": "HIGH",
                        "description": f"Kendall's tau: {tau} (target >= 0.90), Pairwise Acc: {pair_acc} (target >= 0.95)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-ORD-003",
                "title": "Reading order audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 4: Table Reconstruction Benchmark
        try:
            tab_path = reports_dir / "TABLE_RECONSTRUCTION_REPORT.json"
            if not tab_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-TAB-001",
                    "title": "Table reconstruction report missing",
                    "severity": "HIGH",
                    "description": f"Missing {tab_path}",
                })
            else:
                with open(tab_path, "r", encoding="utf-8") as f:
                    tab_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(tab_data, bench_schema)
                m = tab_data.get("metrics", {})
                teds = m.get("teds_score", 0.0)
                cell_acc = m.get("cell_exact_match_ratio", 0.0)
                if teds >= 0.90 and cell_acc >= 0.95:
                    passed += 1
                    artifacts.append({
                        "name": "table_reconstruction_report",
                        "path": str(tab_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-TAB-002",
                        "title": "Table reconstruction score below quality gate",
                        "severity": "HIGH",
                        "description": f"TEDS: {teds} (target >= 0.90), Cell Acc: {cell_acc} (target >= 0.95)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-TAB-003",
                "title": "Table reconstruction audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 5: Normalization & Provenance Hard Invariants
        try:
            norm_path = reports_dir / "NORMALIZATION_VALIDATION.json"
            prov_path = reports_dir / "PROVENANCE_AUDIT.json"
            if not norm_path.exists() or not prov_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-PRV-001",
                    "title": "Normalization or Provenance audit reports missing",
                    "severity": "HIGH",
                    "description": f"Missing {norm_path} or {prov_path}",
                })
            else:
                with open(prov_path, "r", encoding="utf-8") as f:
                    prov_data = json.load(f)
                m = prov_data.get("metrics", {})
                all_inv_pass = m.get("all_invariants_passed", False)
                violations = m.get("violations_count", -1)
                if all_inv_pass is True and violations == 0:
                    passed += 1
                    artifacts.append({
                        "name": "normalization_report",
                        "path": str(norm_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "provenance_audit",
                        "path": str(prov_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-PRV-002",
                        "title": "Provenance hard invariants check failed",
                        "severity": "CRITICAL",
                        "description": f"All Invariants Passed: {all_inv_pass}, violations: {violations}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-PRV-003",
                "title": "Provenance invariants audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 6: Malformed Document Security & Sandbox Containment
        try:
            mal_path = reports_dir / "MALFORMED_DOCUMENT_SECURITY_REPORT.json"
            if not mal_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-SEC-001",
                    "title": "Malformed document security report missing",
                    "severity": "HIGH",
                    "description": f"Missing {mal_path}",
                })
            else:
                with open(mal_path, "r", encoding="utf-8") as f:
                    mal_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(mal_data, bench_schema)
                m = mal_data.get("metrics", {})
                rate = m.get("containment_success_rate", 0.0)
                crash_rate = m.get("unhandled_crash_rate", 1.0)
                sanitization = m.get("error_sanitization_compliance", 0.0)
                if rate == 1.0 and crash_rate == 0.0 and sanitization == 1.0:
                    passed += 1
                    artifacts.append({
                        "name": "malformed_document_security_report",
                        "path": str(mal_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-SEC-002",
                        "title": "Malformed document security vulnerabilities detected",
                        "severity": "CRITICAL",
                        "description": f"Containment rate: {rate}, Crash rate: {crash_rate}, Sanitization: {sanitization}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-SEC-003",
                "title": "Malformed document security audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 7: End-to-End Pipeline Performance
        try:
            perf_path = reports_dir / "PROCESSING_PERFORMANCE_REPORT.json"
            if not perf_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-PROC-PRF-001",
                    "title": "Processing performance report missing",
                    "severity": "HIGH",
                    "description": f"Missing {perf_path}",
                })
            else:
                with open(perf_path, "r", encoding="utf-8") as f:
                    perf_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(perf_data, bench_schema)
                m = perf_data.get("metrics", {})
                throughput = m.get("throughput_pages_per_sec", 0.0)
                lat_median = m.get("latency_per_doc_median_ms", 99999.0)
                if throughput >= 5.0 and lat_median <= 1000.0:
                    passed += 1
                    artifacts.append({
                        "name": "processing_performance_report",
                        "path": str(perf_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-PROC-PRF-002",
                        "title": "Pipeline throughput or latency below performance baseline",
                        "severity": "MEDIUM",
                        "description": f"Throughput: {throughput} p/s (target >= 5.0), Median Latency: {lat_median} ms (target <= 1000 ms)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-PROC-PRF-003",
                "title": "Processing performance audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        status = "PASSED" if failed == 0 else "FAILED"
        return {
            "status": status,
            "statistics": {
                "total": passed + failed,
                "passed": passed,
                "failed": failed,
                "skipped": 0,
                "errors": 0,
            },
            "findings": findings,
            "artifacts": artifacts,
        }
