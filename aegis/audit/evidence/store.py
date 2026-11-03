"""
aegis/audit/evidence/store.py
=============================
Evidence store persisting and reading structured audit runs and artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis.audit.evidence.hashing import hash_bytes, hash_file
from aegis.audit.evidence.models import AuditArtifact, AuditRun, AuditSummary
from aegis.audit.evidence.validator import EvidenceValidator
from aegis.audit.runner.exceptions import EvidenceValidationError


class EvidenceStore:
    """Manages filesystem storage, serialization, and retrieval of audit runs."""

    def __init__(self, base_artifacts_dir: Optional[Path] = None) -> None:
        if base_artifacts_dir is None:
            # Default to repo root artifacts/audits
            root = Path(__file__).resolve().parent.parent.parent.parent
            base_artifacts_dir = root / "artifacts" / "audits"
        self.base_dir = Path(base_artifacts_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_run_dir(self, run_id: str) -> Path:
        # AG-YYYYMMDD-HHMMSS-<SUFFIX>
        parts = run_id.split("-")
        if len(parts) >= 2 and len(parts[1]) == 8:
            year = parts[1][:4]
            month = parts[1][4:6]
            return self.base_dir / year / month / run_id
        return self.base_dir / "runs" / run_id

    def save_run(
        self,
        run: AuditRun,
        summary: Optional[AuditSummary] = None,
        summary_md: Optional[str] = None,
        provenance_dict: Optional[Dict[str, Any]] = None,
    ) -> Path:
        run_data = run.to_dict()
        run_dir = self._resolve_run_dir(run.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        # Validate before write
        errors = EvidenceValidator.validate_run(run_data, root_dir=run_dir)
        if errors:
            raise EvidenceValidationError(f"Evidence validation failed: {'; '.join(errors)}")

        # 1. Save run.json
        (run_dir / "run.json").write_text(json.dumps(run_data, indent=2), encoding="utf-8")

        # 2. Save summary.json & summary.md
        if summary:
            (run_dir / "summary.json").write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
        if summary_md:
            (run_dir / "summary.md").write_text(summary_md, encoding="utf-8")

        # 3. Save provenance.json
        if provenance_dict:
            (run_dir / "provenance.json").write_text(json.dumps(provenance_dict, indent=2), encoding="utf-8")

        # 4. Save per-suite results
        suites_dir = run_dir / "suites"
        suites_dir.mkdir(exist_ok=True)
        for s in run.suites:
            sid = s.get("suite_id", "unknown").lower()
            (suites_dir / f"{sid}.json").write_text(json.dumps(s, indent=2), encoding="utf-8")

        # 5. Save findings
        findings_dir = run_dir / "findings"
        findings_dir.mkdir(exist_ok=True)
        (findings_dir / "findings.json").write_text(json.dumps(run.findings, indent=2), encoding="utf-8")

        return run_dir

    def save_artifact_file(
        self,
        run_id: str,
        artifact_id: str,
        filename: str,
        content: str | bytes,
        artifact_type: str = "LOG",
        suite_id: Optional[str] = None,
        created_at: str = "",
    ) -> AuditArtifact:
        run_dir = self._resolve_run_dir(run_id)
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        target_file = artifacts_dir / filename
        data_bytes = content.encode("utf-8") if isinstance(content, str) else content
        target_file.write_bytes(data_bytes)

        sha = hash_bytes(data_bytes)
        rel_path = f"artifacts/{filename}"

        return AuditArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            suite_id=suite_id,
            artifact_type=artifact_type,
            filename=filename,
            relative_path=rel_path,
            sha256=sha,
            size_bytes=len(data_bytes),
            created_at=created_at,
        )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        run_dir = self._resolve_run_dir(run_id)
        run_file = run_dir / "run.json"
        if not run_file.is_file():
            # Try searching in base_dir recursively
            matches = list(self.base_dir.rglob(f"{run_id}/run.json"))
            if matches:
                run_file = matches[0]
            else:
                return None
        return json.loads(run_file.read_text(encoding="utf-8"))

    def verify_integrity(self, run_id: str) -> Dict[str, Any]:
        run_data = self.get_run(run_id)
        if not run_data:
            return {"status": "NOT_FOUND", "run_id": run_id, "errors": ["Run not found"]}

        run_dir = self._resolve_run_dir(run_id)
        errors = EvidenceValidator.validate_run(run_data, root_dir=run_dir)
        return {
            "status": "PASS" if not errors else "INTEGRITY_FAILURE",
            "run_id": run_id,
            "errors": errors
        }

    def list_runs(self) -> List[str]:
        runs = []
        for path in self.base_dir.rglob("run.json"):
            runs.append(path.parent.name)
        return sorted(runs, reverse=True)
