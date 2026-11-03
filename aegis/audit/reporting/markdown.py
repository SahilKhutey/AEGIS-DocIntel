"""
aegis/audit/reporting/markdown.py
=================================
Generates human-readable GitHub-flavored Markdown execution summaries.
"""

from __future__ import annotations

from typing import Any, Dict
from aegis.audit.evidence.models import AuditSummary


def generate_markdown_summary(run_data: Dict[str, Any], summary: AuditSummary) -> str:
    source = run_data.get("source", {})
    env = run_data.get("environment", {})
    cfg = run_data.get("configuration", {})
    suites = run_data.get("suites", [])
    findings = run_data.get("findings", [])

    lines = [
        f"# AEGIS-DocIntel — Audit Execution Report ({summary.run_id})",
        "",
        f"**Run Status**: `{summary.status}`  ",
        f"**Duration**: `{summary.duration_seconds}s`  ",
        f"**Commit**: `{source.get('commit_sha', 'UNKNOWN')}` ({source.get('branch', 'DETACHED')})  ",
        f"**Working Tree**: `{'CLEAN' if source.get('working_tree_clean') else 'MODIFIED'}`  ",
        f"**Configuration Profile**: `{cfg.get('profile', 'default')}` (`{cfg.get('hash', '')[:12]}`)  ",
        f"**Completion Ratio**: `{summary.completion_ratio}%`  ",
        "",
        "---",
        "",
        "## Suite Execution Summary",
        "",
        "| Suite ID | Status | Total | Passed | Failed | Skipped | Errors | Duration |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for s in suites:
        stats = s.get("statistics", {})
        lines.append(
            f"| `{s.get('suite_id')}` | **{s.get('status')}** | {stats.get('total', 0)} | {stats.get('passed', 0)} | {stats.get('failed', 0)} | {stats.get('skipped', 0)} | {stats.get('errors', 0)} | {s.get('duration_seconds', 0.0)}s |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Findings Overview",
        f"- **Total Findings**: {summary.total_findings}",
        f"- **Critical Severity**: {summary.critical_findings}",
        f"- **High Severity**: {summary.high_findings}",
        "",
    ])

    if findings:
        lines.extend([
            "| Finding ID | Suite | Severity | Title |",
            "| :--- | :--- | :---: | :--- |",
        ])
        for f in findings:
            lines.append(f"| `{f.get('finding_id')}` | `{f.get('suite_id')}` | **{f.get('severity')}** | {f.get('title')} |")
    else:
        lines.append("*Zero findings detected across all executed suites.*")

    lines.append("")
    return "\n".join(lines)
