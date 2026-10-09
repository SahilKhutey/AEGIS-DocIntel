#!/usr/bin/env python3
"""
scripts/pilot_dashboard.py — Minimal, Honest Pilot Feedback Tracking Tool
===========================================================================
Aggregates GitHub issues labeled 'pilot-feedback' (via GitHub CLI) or
local feedback entries from 'docs/pilot/feedback_logs.json'.

Cross-references reported issues against STATUS.md known issues to separate
known architectural gaps from genuinely novel findings.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

KNOWN_ISSUE_CATEGORIES = {
    "IN_MEMORY_PERSISTENCE": "Document metadata stored in process memory only (lost on restart)",
    "OPTIONAL_EMBEDDINGS": "Sentence-transformers / torch large download when full ML is requested",
    "COLD_START_DEPENDENCY": "Dev dependencies required for pytest suite",
    "TABLE_COMPLEXITY": "Non-standard table bounding box alignment in scanned PDFs",
}


def get_github_issues() -> List[Dict[str, Any]]:
    """Attempts to fetch pilot feedback issues using the GitHub CLI."""
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--label",
                "pilot-feedback",
                "--json",
                "number,title,body,createdAt,author,state",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
        return []


def get_local_feedback() -> List[Dict[str, Any]]:
    """Loads offline feedback logs from docs/pilot/feedback_logs.json if available."""
    local_path = Path(__file__).parent.parent / "docs" / "pilot" / "feedback_logs.json"
    if local_path.is_file():
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def categorize_issue(text: str) -> str:
    """Matches text against known issues in STATUS.md."""
    lower = text.lower()
    if "memory" in lower and ("restart" in lower or "lost" in lower or "persist" in lower):
        return "IN_MEMORY_PERSISTENCE"
    if "torch" in lower or "download" in lower or "large" in lower or "disk" in lower:
        return "OPTIONAL_EMBEDDINGS"
    if "pytest" in lower or "cold-start" in lower or "missing module" in lower:
        return "COLD_START_DEPENDENCY"
    if "table" in lower or "scanned" in lower or "column" in lower:
        return "TABLE_COMPLEXITY"
    return "NEW_UNTRACKED_BUG"


def generate_report(feedbacks: List[Dict[str, Any]]) -> None:
    print("=" * 70)
    print(" AEGIS-DocIntel / aegis-docprep — Pilot Feedback Dashboard")
    print("=" * 70)
    print(f"Total Pilot Reports Tracked: {len(feedbacks)}\n")

    if not feedbacks:
        print("No pilot feedback recorded yet.")
        print("To record offline feedback, populate docs/pilot/feedback_logs.json.")
        return

    component_counts: Dict[str, int] = {}
    satisfaction_counts: Dict[str, int] = {"yes": 0, "partial": 0, "no": 0}
    issue_categories: Dict[str, int] = {}

    for item in feedbacks:
        author = item.get("author", {}).get("login", item.get("pilot_name", "anonymous"))
        component = item.get("component", "aegis-docprep")
        date = item.get("createdAt", item.get("date", "2026-10"))[:10]
        title = item.get("title", "Pilot evaluation")
        use_again = str(item.get("would_use_again", "yes")).lower()

        component_counts[component] = component_counts.get(component, 0) + 1
        if use_again in satisfaction_counts:
            satisfaction_counts[use_again] += 1

        body = item.get("body", item.get("details", ""))
        cat = categorize_issue(body + " " + title)
        issue_categories[cat] = issue_categories.get(cat, 0) + 1

        status_marker = "[KNOWN]" if cat != "NEW_UNTRACKED_BUG" else "[NEW!]"
        print(f"[{date}] {author:<16} | {component:<15} | {status_marker} {title}")

    print("\n--- Summary Breakdown ---")
    print("Component Usage:")
    for comp, count in component_counts.items():
        print(f"  - {comp}: {count}")

    print("\nWould Use Again:")
    for k, v in satisfaction_counts.items():
        print(f"  - {k.capitalize()}: {v}")

    print("\nReported Friction Categorization:")
    for cat, count in issue_categories.items():
        desc = KNOWN_ISSUE_CATEGORIES.get(cat, "Novel issue — requires fresh investigation")
        print(f"  - {cat} ({count}): {desc}")

    print("=" * 70)


def main() -> None:
    feedbacks = get_github_issues()
    if not feedbacks:
        feedbacks = get_local_feedback()
    generate_report(feedbacks)


if __name__ == "__main__":
    main()
