"""
aegis/audit/suites/intelligence.py
==================================
Audit suite executing Document Intelligence capability validations:
Retrieval Modes, Golden Question Dataset, Citation Correctness,
Abstention & Unanswerable Handling, Fact Extraction & Conflict Detection,
and Evidence-Backed Multi-Format Report Generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
import jsonschema

from aegis.audit.suites.base import BaseAuditSuite
from aegis.intelligence.questions import GoldenQuestionLoader, QuestionPartitioner


class IntelligenceAuditSuite(BaseAuditSuite):
    suite_id = "intelligence"
    suite_name = "Document Intelligence and Reasoning Audit Suite"
    suite_version = "1.0.0"
    description = (
        "Verifies multi-modal retrieval benchmarks, golden question integrity, "
        "claim-level citation support, abstention & unanswerable handling, "
        "fact extraction, conflict detection, and multi-format report generation."
    )
    tags = [
        "intelligence",
        "retrieval",
        "questions",
        "citations",
        "abstention",
        "facts",
        "conflicts",
        "reports",
    ]

    def validate(self, context: Any) -> None:
        """Verify presence of intelligence configurations and schemas."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        cfg_dir = root / "configs" / "intelligence"
        schema_dir = root / "schemas" / "intelligence"
        if not cfg_dir.exists():
            raise FileNotFoundError(f"Intelligence configuration directory not found at {cfg_dir}")
        if not schema_dir.exists():
            raise FileNotFoundError(f"Intelligence schema directory not found at {schema_dir}")

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute all intelligence capability audit checks."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        reports_dir = root / "artifacts" / "intelligence" / "reports"
        schema_dir = root / "schemas" / "intelligence"
        data_dir = root / "data" / "intelligence"
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

        # Check 1: Retrieval Modes Benchmark
        try:
            ret_path = reports_dir / "RETRIEVAL_MODES_BENCHMARK.json"
            if not ret_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-RET-001",
                    "title": "Retrieval Modes benchmark report missing",
                    "severity": "HIGH",
                    "description": f"Missing {ret_path}",
                })
            else:
                with open(ret_path, "r", encoding="utf-8") as f:
                    ret_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(ret_data, bench_schema)
                m = ret_data.get("metrics", {})
                mrr = m.get("hybrid_mrr", 0.0)
                recall_5 = m.get("hybrid_recall_at_5", 0.0)
                lat_median = m.get("hybrid_latency_median_ms", 9999.0)
                if recall_5 >= 0.80 and mrr >= 0.60 and lat_median <= 50.0:
                    passed += 1
                    artifacts.append({
                        "name": "retrieval_modes_benchmark",
                        "path": str(ret_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-RET-002",
                        "title": "Retrieval performance below quality thresholds",
                        "severity": "HIGH",
                        "description": f"Recall@5: {recall_5} (target >= 0.80), MRR: {mrr} (target >= 0.60), Latency: {lat_median}ms (target <= 50ms)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-RET-003",
                "title": "Retrieval modes audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 2: Golden Question Dataset Integrity & Partition Leakage
        try:
            gq_path = data_dir / "golden_questions.jsonl"
            card_path = reports_dir / "GOLDEN_DATASET_CARD.md"
            if not gq_path.exists() or not card_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-QST-001",
                    "title": "Golden question dataset or dataset card missing",
                    "severity": "HIGH",
                    "description": f"gq_path: {gq_path.exists()}, card_path: {card_path.exists()}",
                })
            else:
                loader = GoldenQuestionLoader()
                qs = loader.load_jsonl(gq_path, validate_schema=True)
                task_types = {q.task_type for q in qs}

                partitioner = QuestionPartitioner(seed=20261103)
                splits = partitioner.partition(qs, dev_ratio=0.60, val_ratio=0.20)
                dev_docs = {doc for q in splits["development"] for doc in q.document_scope}
                val_docs = {doc for q in splits["validation"] for doc in q.document_scope}
                holdout_docs = {doc for q in splits["holdout"] for doc in q.document_scope}

                leakage = (
                    len(dev_docs.intersection(val_docs)) > 0
                    or len(dev_docs.intersection(holdout_docs)) > 0
                    or len(val_docs.intersection(holdout_docs)) > 0
                )

                if len(qs) >= 130 and len(task_types) >= 9 and not leakage:
                    passed += 1
                    artifacts.append({
                        "name": "golden_questions_dataset",
                        "path": str(gq_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "golden_dataset_card",
                        "path": str(card_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-QST-002",
                        "title": "Golden question count, taxonomy coverage, or partition leakage violation",
                        "severity": "HIGH",
                        "description": f"Records: {len(qs)} (target >= 130), Categories: {len(task_types)} (target >= 9), Leakage: {leakage}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-QST-003",
                "title": "Golden question dataset audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 3: Claim-Level Citation Correctness
        try:
            cit_path = reports_dir / "CITATION_CORRECTNESS_REPORT.json"
            if not cit_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-CIT-001",
                    "title": "Citation correctness report missing",
                    "severity": "HIGH",
                    "description": f"Missing {cit_path}",
                })
            else:
                with open(cit_path, "r", encoding="utf-8") as f:
                    cit_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(cit_data, bench_schema)
                m = cit_data.get("metrics", {})
                prec = m.get("citation_precision", 0.0)
                supp = m.get("claim_support_rate", 0.0)
                acc = m.get("label_classification_accuracy", 0.0)
                unsupp = m.get("unsupported_claim_rate", 1.0)
                if prec >= 0.90 and supp >= 0.90 and acc >= 0.95 and unsupp <= 0.05:
                    passed += 1
                    artifacts.append({
                        "name": "citation_correctness_report",
                        "path": str(cit_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-CIT-002",
                        "title": "Citation correctness quality gates not met",
                        "severity": "HIGH",
                        "description": f"Precision: {prec} (target >= 0.90), Support: {supp} (target >= 0.90), Label Acc: {acc} (target >= 0.95), Unsupported: {unsupp} (target <= 0.05)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-CIT-003",
                "title": "Citation correctness audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 4: Abstention and Unanswerable Evaluation
        try:
            abs_path = reports_dir / "ABSTENTION_EVALUATION_REPORT.json"
            if not abs_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-ABS-001",
                    "title": "Abstention evaluation report missing",
                    "severity": "HIGH",
                    "description": f"Missing {abs_path}",
                })
            else:
                with open(abs_path, "r", encoding="utf-8") as f:
                    abs_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(abs_data, bench_schema)
                m = abs_data.get("metrics", {})
                prec = m.get("abstention_precision", 0.0)
                rec = m.get("abstention_recall", 0.0)
                risk = m.get("selective_risk", 1.0)
                unsupp = m.get("unsupported_answer_rate", 1.0)
                if prec >= 0.90 and rec >= 0.90 and risk <= 0.05 and unsupp <= 0.05:
                    passed += 1
                    artifacts.append({
                        "name": "abstention_evaluation_report",
                        "path": str(abs_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-ABS-002",
                        "title": "Abstention and unanswerable handling quality gates not met",
                        "severity": "HIGH",
                        "description": f"Precision: {prec} (target >= 0.90), Recall: {rec} (target >= 0.90), Selective Risk: {risk} (target <= 0.05), Unsupported: {unsupp} (target <= 0.05)",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-ABS-003",
                "title": "Abstention evaluation audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 5: Fact Extraction & Conflict Detection
        try:
            fct_path = reports_dir / "FACT_EXTRACTION_REPORT.json"
            cnf_path = reports_dir / "CONFLICT_DETECTION_REPORT.json"
            if not fct_path.exists() or not cnf_path.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-FCT-001",
                    "title": "Fact extraction or conflict detection report missing",
                    "severity": "HIGH",
                    "description": f"fct_path: {fct_path.exists()}, cnf_path: {cnf_path.exists()}",
                })
            else:
                with open(fct_path, "r", encoding="utf-8") as f:
                    fct_data = json.load(f)
                with open(cnf_path, "r", encoding="utf-8") as f:
                    cnf_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(fct_data, bench_schema)
                    jsonschema.validate(cnf_data, bench_schema)
                
                fm = fct_data.get("metrics", {})
                f_acc = fm.get("predicate_extraction_accuracy", 0.0)
                f_f1 = fm.get("entity_detection_f1", 0.0)
                f_raw = fm.get("raw_value_preservation_ratio", 0.0)

                cm = cnf_data.get("metrics", {})
                c_acc = cm.get("conflict_classification_accuracy", 0.0)
                c_prec = cm.get("conflict_precision", 0.0)
                c_rec = cm.get("conflict_recall", 0.0)

                if (
                    f_acc >= 0.90 and f_f1 >= 0.90 and f_raw >= 0.90
                    and c_acc >= 0.90 and c_prec >= 0.90 and c_rec >= 0.90
                ):
                    passed += 1
                    artifacts.append({
                        "name": "fact_extraction_report",
                        "path": str(fct_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "conflict_detection_report",
                        "path": str(cnf_path.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-FCT-002",
                        "title": "Fact extraction or conflict detection quality gates not met",
                        "severity": "HIGH",
                        "description": f"Fact Acc: {f_acc}, Entity F1: {f_f1}, Conflict Acc: {c_acc}, Conflict Prec: {c_prec}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-FCT-003",
                "title": "Fact extraction and conflict detection audit evaluation failed",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 6: Report Generation & Multi-Format Rendering
        try:
            rep_path = reports_dir / "REPORT_GENERATION_REPORT.json"
            sample_md = reports_dir / "sample_comparative_report.md"
            if not rep_path.exists() or not sample_md.exists():
                failed += 1
                findings.append({
                    "finding_id": "FIND-INTEL-REP-001",
                    "title": "Report generation benchmark or sample Markdown missing",
                    "severity": "HIGH",
                    "description": f"rep_path: {rep_path.exists()}, sample_md: {sample_md.exists()}",
                })
            else:
                with open(rep_path, "r", encoding="utf-8") as f:
                    rep_data = json.load(f)
                if bench_schema:
                    jsonschema.validate(rep_data, bench_schema)
                m = rep_data.get("metrics", {})
                struct_val = m.get("structural_validity_rate", 0.0)
                cit_val = m.get("citation_validity_rate", 0.0)
                cnf_val = m.get("conflict_preservation_rate", 0.0)
                md_ok = m.get("markdown_render_success", False)
                html_ok = m.get("html_render_success", False)
                json_ok = m.get("json_schema_conformance_rate", 0.0)

                if (
                    struct_val == 1.0 and cit_val == 1.0 and cnf_val == 1.0
                    and md_ok and html_ok and json_ok == 1.0
                ):
                    passed += 1
                    artifacts.append({
                        "name": "report_generation_report",
                        "path": str(rep_path.relative_to(root).as_posix()),
                    })
                    artifacts.append({
                        "name": "sample_comparative_report",
                        "path": str(sample_md.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-INTEL-REP-002",
                        "title": "Report generation structural, citation, or format rendering gates not met",
                        "severity": "HIGH",
                        "description": f"Struct: {struct_val}, Citation: {cit_val}, Conflict: {cnf_val}, MD: {md_ok}, HTML: {html_ok}, JSON: {json_ok}",
                    })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-INTEL-REP-003",
                "title": "Report generation audit evaluation failed",
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
