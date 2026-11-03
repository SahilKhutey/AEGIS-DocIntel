"""
aegis/audit/suites/corpus.py
============================
Audit suite executing corpus integrity, governance, checksum, and partition leakage verifications.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from aegis.audit.suites.base import BaseAuditSuite
from aegis.corpus.independent.inventory import IndependentDocumentInventory
from aegis.corpus.integrity.checksum import calculate_sha256
from aegis.corpus.integrity.manifest import ChecksumManifest
from aegis.corpus.partition.grouping import GroupableDocument
from aegis.corpus.partition.leakage import LeakageDetector
from aegis.corpus.partition.splitter import PartitionManifest
from aegis.corpus.registry.acquisition_registry import AcquisitionRegistry
from aegis.corpus.registry.licence_registry import LicenceRegistry
from aegis.corpus.registry.source_registry import SourceRegistry


class CorpusAuditSuite(BaseAuditSuite):
    suite_id = "corpus"
    suite_name = "Corpus Governance and Integrity Audit Suite"
    suite_version = "1.0.0"
    description = "Verifies corpus registry integrity, licence permissions, SHA-256 manifests, and partition leakage."
    tags = ["corpus", "governance", "integrity", "reproducibility"]

    def validate(self, context: Any) -> None:
        """Verify presence of corpus registries and schemas."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        reg_dir = root / "configs" / "corpus"
        if not reg_dir.exists():
            raise FileNotFoundError(f"Corpus configuration directory not found at {reg_dir}")

    def execute(self, context: Any) -> Dict[str, Any]:
        """Execute all corpus audit checks."""
        root = Path(getattr(context, "root_dir", Path.cwd()))
        findings: List[Dict[str, Any]] = []
        artifacts: List[Dict[str, Any]] = []
        passed = 0
        failed = 0

        # Check 1: Licence Registry
        try:
            lic_reg = LicenceRegistry(root / "configs" / "corpus" / "licences.yaml")
            all_lics = lic_reg.list_all()
            if len(all_lics) >= 5:
                passed += 1
            else:
                failed += 1
                findings.append({
                    "finding_id": "FIND-CORPUS-LIC-001",
                    "title": "Insufficient licences in registry",
                    "severity": "HIGH",
                    "description": f"Expected >= 5 licences, found {len(all_lics)}",
                })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-CORPUS-LIC-002",
                "title": "Licence registry validation error",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 2: Source Registry
        try:
            src_reg = SourceRegistry(root / "configs" / "corpus" / "sources.yaml")
            is_valid, errs = src_reg.validate_integrity()
            if not is_valid:
                failed += 1
                findings.append({
                    "finding_id": "FIND-CORPUS-SRC-001",
                    "title": "Source registry integrity errors",
                    "severity": "HIGH",
                    "description": "; ".join(errs),
                })
            else:
                passed += 1
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-CORPUS-SRC-002",
                "title": "Source registry load failure",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 3: Acquisition Registry
        try:
            acq_reg = AcquisitionRegistry(root / "configs" / "corpus" / "acquisition_decisions.yaml")
            all_dec = acq_reg.list_all()
            if len(all_dec) >= 10:
                passed += 1
            else:
                failed += 1
                findings.append({
                    "finding_id": "FIND-CORPUS-ACQ-001",
                    "title": "Insufficient acquisition decisions recorded",
                    "severity": "HIGH",
                    "description": f"Expected >= 10 decisions, found {len(all_dec)}",
                })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-CORPUS-ACQ-002",
                "title": "Acquisition registry validation error",
                "severity": "HIGH",
                "description": str(exc),
            })

        # Check 4: Checksum Manifest Verification
        try:
            checksum_manifest_file = root / "artifacts" / "corpus" / "manifests" / "checksum_manifest.json"
            if checksum_manifest_file.exists():
                with open(checksum_manifest_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                c_manifest = ChecksumManifest(**cdata)
                assert len(c_manifest.artifacts) >= 200
                passed += 1
                artifacts.append({
                    "name": "checksum_manifest",
                    "path": str(checksum_manifest_file.relative_to(root).as_posix()),
                })
            else:
                failed += 1
                findings.append({
                    "finding_id": "FIND-CORPUS-CHK-001",
                    "title": "Checksum manifest missing",
                    "severity": "MEDIUM",
                    "description": f"File not found: {checksum_manifest_file}",
                })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-CORPUS-CHK-002",
                "title": "Checksum manifest verification failed to run",
                "severity": "MEDIUM",
                "description": str(exc),
            })

        # Check 5: Partition Leakage Verification
        try:
            p_manifest_file = root / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
            p_inv_file = root / "artifacts" / "corpus" / "manifests" / "document_inventory.jsonl"
            if p_manifest_file.exists() and p_inv_file.exists():
                with open(p_manifest_file, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                p_manifest = PartitionManifest(**p_data)

                docs = []
                with open(p_inv_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            d = json.loads(line)
                            docs.append(GroupableDocument(
                                document_id=d["document_id"],
                                source_id=d["source_id"],
                                sha256=d["sha256"],
                                title=d.get("title"),
                                publisher=d.get("publisher"),
                            ))

                detector = LeakageDetector()
                report = detector.audit_partitions(p_manifest, docs)
                if report.status == "PASSED":
                    passed += 1
                    artifacts.append({
                        "name": "partition_manifest",
                        "path": str(p_manifest_file.relative_to(root).as_posix()),
                    })
                else:
                    failed += 1
                    findings.append({
                        "finding_id": "FIND-CORPUS-LEAK-001",
                        "title": "Partition leakage violation detected",
                        "severity": "CRITICAL",
                        "description": "; ".join(report.violations),
                    })
            else:
                failed += 1
                findings.append({
                    "finding_id": "FIND-CORPUS-LEAK-002",
                    "title": "Partition manifest or document inventory missing",
                    "severity": "HIGH",
                    "description": f"Missing partition artifacts in {root}/artifacts/corpus/manifests/",
                })
        except Exception as exc:
            failed += 1
            findings.append({
                "finding_id": "FIND-CORPUS-LEAK-003",
                "title": "Partition leakage audit failed to execute",
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
