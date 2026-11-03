"""
aegis/audit/evidence/models.py
==============================
Typed domain models for AEGIS audit evidence entities.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AuditFinding:
    finding_id: str
    run_id: str
    suite_id: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    status: str = "OPEN"
    description: str = ""
    location: Optional[Dict[str, Any]] = None
    evidence_refs: List[str] = field(default_factory=list)
    recommendation: str = ""
    fingerprint: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditArtifact:
    artifact_id: str
    run_id: str
    artifact_type: str
    filename: str
    relative_path: str
    sha256: str
    size_bytes: int
    created_at: str
    suite_id: Optional[str] = None
    media_type: str = "application/octet-stream"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditSuiteResult:
    suite_id: str
    suite_version: str
    status: str  # PASSED, FAILED, ERROR, TIMEOUT, SKIPPED, BLOCKED, CANCELLED
    started_at: str
    completed_at: str
    duration_seconds: float
    statistics: Dict[str, int]
    findings: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnvironmentSnapshot:
    os: str
    architecture: str
    python_version: str
    runner_version: str = "1.0.0"
    python_implementation: str = "CPython"
    dependency_lock_hash: str = ""
    platform_identifier: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommitSnapshot:
    repository: str
    branch: Optional[str]
    commit_sha: str
    working_tree_clean: bool
    remote_url: str = ""
    commit_timestamp: str = ""
    modified_files_count: int = 0
    untracked_files_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfigurationSnapshot:
    profile: str
    sha256: str
    resolved_at: str
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditSummary:
    run_id: str
    status: str
    started_at: str
    completed_at: str
    duration_seconds: float
    planned_suites: int
    executed_suites: int
    passed_suites: int
    failed_suites: int
    completion_ratio: float
    total_findings: int
    critical_findings: int
    high_findings: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditRun:
    run_id: str
    baseline_id: str
    project: str
    execution: Dict[str, Any]
    source: Dict[str, Any]
    configuration: Dict[str, Any]
    environment: Dict[str, Any]
    suites: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
