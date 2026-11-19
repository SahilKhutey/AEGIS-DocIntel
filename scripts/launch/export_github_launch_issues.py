"""
AEGIS-DocIntel — Product Hunt Launch Issue Exporter & Validator

Parses, validates, and serializes the 70 Product Hunt launch tasks,
6 milestones, and label taxonomy into structured JSON for GitHub API / gh CLI batch import.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OPERATIONS_DIR = REPO_ROOT / "launch" / "product-hunt" / "operations"
REGISTER_FILE = OPERATIONS_DIR / "LAUNCH_TASK_REGISTER.md"
OUTPUT_JSON = OPERATIONS_DIR / "github_launch_issues.json"

MILESTONES = [
    {
        "id": "PH-01",
        "title": "PH-01 — Product Readiness",
        "description": "Restore & verify end-to-end document processing pipeline on real files",
        "state": "open",
    },
    {
        "id": "PH-02",
        "title": "PH-02 — Beta Validation",
        "description": "Security boundary audit, tenant isolation, and closed beta onboarding",
        "state": "open",
    },
    {
        "id": "PH-03",
        "title": "PH-03 — Launch Website & Assets",
        "description": "Positioning, marketing copy, landing page, and visual gallery assets",
        "state": "open",
    },
    {
        "id": "PH-04",
        "title": "PH-04 — Release Candidate",
        "description": "Packaged Windows installer, portable ZIP, SBOM, Ed25519 signing & signoff",
        "state": "open",
    },
    {
        "id": "PH-05",
        "title": "PH-05 — Product Hunt Launch",
        "description": "Manual maker submission, launch-day operations, monitoring & support",
        "state": "open",
    },
    {
        "id": "PH-06",
        "title": "PH-06 — Post-Launch Stabilization",
        "description": "Funnel conversion analysis, feedback triage, and defect remediation",
        "state": "open",
    },
]

LABELS = [
    {"name": "launch", "color": "0e8a16", "description": "Product Hunt launch scope"},
    {"name": "launch:p0", "color": "d93f0b", "description": "Blocks launch"},
    {"name": "launch:p1", "color": "fbca04", "description": "Required for a strong launch"},
    {"name": "launch:p2", "color": "0075ca", "description": "Post-launch improvement"},
    {"name": "area:product", "color": "1d76db", "description": "Product functionality"},
    {"name": "area:backend", "color": "5319e7", "description": "Backend and APIs"},
    {"name": "area:frontend", "color": "1d76db", "description": "Frontend"},
    {"name": "area:security", "color": "b60205", "description": "Security and privacy"},
    {"name": "area:release", "color": "0052cc", "description": "Build and distribution"},
    {"name": "area:marketing", "color": "c5def5", "description": "Positioning and listing"},
    {"name": "area:website", "color": "bfdadc", "description": "Landing page"},
    {"name": "area:assets", "color": "d4c5f9", "description": "Logo, gallery, video and graphics"},
    {"name": "area:analytics", "color": "006b75", "description": "Metrics and reporting"},
    {"name": "area:beta", "color": "f9d0c4", "description": "Beta users and feedback"},
    {"name": "type:bug", "color": "d73a4a", "description": "Defect"},
    {"name": "type:task", "color": "a2eeef", "description": "Execution task"},
    {"name": "type:research", "color": "d4c5f9", "description": "Research"},
    {"name": "type:documentation", "color": "0075ca", "description": "Documentation"},
    {"name": "status:blocked", "color": "e11d21", "description": "Waiting on a dependency"},
    {"name": "status:needs-verification", "color": "e99695", "description": "Evidence not yet available"},
]


def parse_tasks_from_register(markdown_path: Path) -> List[Dict[str, Any]]:
    """Parse tasks from markdown table rows in LAUNCH_TASK_REGISTER.md."""
    if not markdown_path.exists():
        raise FileNotFoundError(f"Register file not found: {markdown_path}")

    content = markdown_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    tasks: List[Dict[str, Any]] = []
    # Match markdown table row: | `PH-001` | Title | Work | DoD | Priority | Mode | Target Milestone |
    row_pattern = re.compile(
        r"^\|\s*`?(PH-\d{3})`?\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\|\s*`?([^|`]+)`?\s*\|"
    )

    for line in lines:
        match = row_pattern.match(line.strip())
        if match:
            task_id = match.group(1).strip()
            title = match.group(2).strip()
            work = match.group(3).strip()
            dod = match.group(4).strip()
            priority = match.group(5).strip()
            mode = match.group(6).strip().replace("**", "")
            milestone = match.group(7).strip()

            tasks.append({
                "id": task_id,
                "title": f"[{task_id}] {title}",
                "body": (
                    f"### Scope of Work\n{work}\n\n"
                    f"### Definition of Done\n{dod}\n\n"
                    f"### Target Milestone\n{milestone}\n\n"
                    f"### Execution Mode\n{mode}\n"
                ),
                "labels": ["launch", priority, "type:task"],
                "milestone": milestone,
                "priority": priority,
                "mode": mode,
                "work": work,
                "definition_of_done": dod,
            })

    return tasks


def validate_launch_inventory(tasks: List[Dict[str, Any]]) -> None:
    """Validate that the full 70-task launch register is sound."""
    if len(tasks) != 70:
        raise ValueError(f"Expected 70 launch tasks, but found {len(tasks)}")

    expected_ids = [f"PH-{i:03d}" for i in range(1, 71)]
    found_ids = [t["id"] for t in tasks]

    if found_ids != expected_ids:
        missing = set(expected_ids) - set(found_ids)
        extra = set(found_ids) - set(expected_ids)
        raise ValueError(f"Task ID mismatch. Missing: {missing}, Extra: {extra}")

    valid_priorities = {"launch:p0", "launch:p1", "launch:p2"}
    for task in tasks:
        if task["priority"] not in valid_priorities:
            raise ValueError(f"Invalid priority '{task['priority']}' for task {task['id']}")
        if not task["work"]:
            raise ValueError(f"Empty work description for task {task['id']}")
        if not task["definition_of_done"]:
            raise ValueError(f"Empty DoD for task {task['id']}")


def export_issues() -> Path:
    """Export validated launch tasks, milestones, and labels to JSON."""
    tasks = parse_tasks_from_register(REGISTER_FILE)
    validate_launch_inventory(tasks)

    payload = {
        "project_name": "AEGIS-DocIntel — Product Hunt Launch Control Center",
        "milestones": MILESTONES,
        "labels": LABELS,
        "task_count": len(tasks),
        "tasks": tasks,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Successfully validated and exported {len(tasks)} launch tasks to {OUTPUT_JSON}")
    return OUTPUT_JSON


if __name__ == "__main__":
    try:
        export_issues()
    except Exception as exc:
        print(f"Error during launch issue export: {exc}", file=sys.stderr)
        sys.exit(1)
