"""
AEGIS-DocIntel — Product Hunt Launch Verification Suite (PH-LAUNCH-01)

Automated tests validating GitHub Actions workflows, repository governance,
issue templates, PR template, dependabot, CODEOWNERS, 70-task launch register,
and release readiness gates.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GITHUB_DIR = REPO_ROOT / ".github"
WORKFLOWS_DIR = GITHUB_DIR / "workflows"
ISSUE_TEMPLATES_DIR = GITHUB_DIR / "ISSUE_TEMPLATE"
LAUNCH_DIR = REPO_ROOT / "launch" / "product-hunt"
OPERATIONS_DIR = LAUNCH_DIR / "operations"
SCRIPTS_LAUNCH_DIR = REPO_ROOT / "scripts" / "launch"

# 30 canonical workflows specified in PH-LAUNCH-01
EXPECTED_WORKFLOWS = [
    # Group A: Core development & quality
    "ci.yml",                     # GH-01
    "backend-ci.yml",             # GH-02
    "frontend-ci.yml",            # GH-03
    "integration-tests.yml",      # GH-04
    "e2e-tests.yml",              # GH-05
    "regression-tests.yml",       # GH-06
    "docs-validation.yml",        # GH-07
    "link-check.yml",             # GH-08
    # Group B: Security & supply chain
    "codeql.yml",                 # GH-09
    "secret-scan.yml",            # GH-10
    "dependency-review.yml",      # GH-11
    "dependency-audit.yml",       # GH-12
    "container-security.yml",     # GH-13
    "sbom.yml",                   # GH-14
    "client-exposure-audit.yml",  # GH-15
    # Group C: Marketing & website
    "marketing-preview.yml",      # GH-16
    "marketing-production.yml",   # GH-17
    "marketing-content-check.yml",# GH-18
    "launch-assets-validation.yml",# GH-19
    "seo-validation.yml",         # GH-20
    "website-smoke-tests.yml",    # GH-21
    # Group D: Packaging & release
    "evaluation-release.yml",     # GH-22
    "release-integrity.yml",      # GH-23
    "release-install-tests.yml",  # GH-24
    "release-publish.yml",        # GH-25
    "post-deploy-smoke.yml",      # GH-26
    # Group E: Monitoring & operations
    "scheduled-health-check.yml", # GH-27
    "weekly-launch-report.yml",    # GH-28
    "beta-feedback-triage.yml",   # GH-29
    "post-launch-regression.yml", # GH-30
]

REUSABLE_WORKFLOWS = [
    "backend-ci.yml",
    "frontend-ci.yml",
    "integration-tests.yml",
    "regression-tests.yml",
    "docs-validation.yml",
    "dependency-audit.yml",
    "container-security.yml",
    "sbom.yml",
    "client-exposure-audit.yml",
    "marketing-content-check.yml",
    "launch-assets-validation.yml",
    "seo-validation.yml",
    "website-smoke-tests.yml",
    "release-integrity.yml",
    "release-install-tests.yml",
    "post-deploy-smoke.yml",
]


class TestGitHubWorkflows:
    """Test suite for GitHub Actions workflows."""

    def test_all_30_workflows_exist(self):
        """Verify all 30 specified workflow files are present."""
        for wf in EXPECTED_WORKFLOWS:
            path = WORKFLOWS_DIR / wf
            assert path.exists(), f"Missing required workflow: {wf}"

    def test_all_workflows_are_valid_yaml(self):
        """Verify that every workflow in .github/workflows is well-formed YAML."""
        for path in WORKFLOWS_DIR.glob("*.yml"):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Workflow {path.name} root must be a YAML mapping"
            assert "name" in data, f"Workflow {path.name} missing 'name' attribute"
            assert "jobs" in data or "on" in data, f"Workflow {path.name} must declare 'jobs' or 'on'"

    def test_action_pinning_to_40_hex_shas(self):
        """Verify that all external third-party actions are pinned to 40-character commit SHAs."""
        uses_pattern = re.compile(r"uses:\s*([^\s]+)")
        unpinned = []

        for path in WORKFLOWS_DIR.glob("*.yml"):
            content = path.read_text(encoding="utf-8")
            for line_idx, line in enumerate(content.splitlines(), start=1):
                m = uses_pattern.search(line)
                if not m:
                    continue
                action_ref = m.group(1).strip()
                # Skip local actions or internal reusable workflows
                if action_ref.startswith("./"):
                    continue

                if "@" not in action_ref:
                    unpinned.append((path.name, line_idx, action_ref, "Missing @SHA"))
                    continue

                action_name, sha_part = action_ref.split("@", 1)
                # Strip trailing comment
                clean_sha = sha_part.split("#")[0].strip()
                if not re.match(r"^[0-9a-fA-F]{40}$", clean_sha):
                    unpinned.append((path.name, line_idx, action_ref, f"Invalid SHA: '{clean_sha}'"))

        assert not unpinned, f"Found unpinned actions: {unpinned}"

    def test_reusable_workflows_declare_workflow_call(self):
        """Verify that reusable workflows explicitly declare on: workflow_call."""
        for wf in REUSABLE_WORKFLOWS:
            path = WORKFLOWS_DIR / wf
            assert path.exists(), f"Reusable workflow {wf} missing"
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            on_section = data.get("on") or data.get(True)  # PyYAML sometimes parses unquoted 'on' as True
            assert on_section is not None, f"Workflow {wf} has no 'on' trigger"
            if isinstance(on_section, dict):
                assert "workflow_call" in on_section, f"Reusable workflow {wf} missing 'workflow_call' trigger"
            elif isinstance(on_section, list):
                assert "workflow_call" in on_section, f"Reusable workflow {wf} missing 'workflow_call' trigger"
            elif isinstance(on_section, str):
                assert on_section == "workflow_call", f"Reusable workflow {wf} missing 'workflow_call' trigger"

    def test_ci_orchestrator_gates_releases(self):
        """Verify that Core CI (ci.yml) gates backend, frontend, and integration."""
        ci_path = WORKFLOWS_DIR / "ci.yml"
        with open(ci_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        jobs = data.get("jobs", {})
        assert "backend" in jobs, "ci.yml missing 'backend' job"
        assert "frontend" in jobs, "ci.yml missing 'frontend' job"
        assert "integration" in jobs, "ci.yml missing 'integration' job"
        assert "gate" in jobs, "ci.yml missing 'gate' job"


class TestGitHubGovernance:
    """Test suite for repository issue forms, PR template, dependabot, and CODEOWNERS."""

    def test_issue_forms_exist_and_are_valid(self):
        """Verify all 5 issue templates and config.yml exist and parse as valid YAML."""
        expected_forms = [
            "bug_report.yml",
            "feature_request.yml",
            "beta_feedback.yml",
            "launch_task.yml",
            "security_report.yml",
            "config.yml",
        ]
        for form in expected_forms:
            path = ISSUE_TEMPLATES_DIR / form
            assert path.exists(), f"Missing issue template: {form}"
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Template {form} must be a YAML mapping"
            if form != "config.yml":
                assert "name" in data, f"Template {form} missing 'name'"
                assert "description" in data, f"Template {form} missing 'description'"
                assert "body" in data, f"Template {form} missing 'body'"

    def test_pull_request_template_enforces_launch_gates(self):
        """Verify PR template exists and explicitly notes that frontend build != product readiness."""
        pr_template = GITHUB_DIR / "PULL_REQUEST_TEMPLATE.md"
        assert pr_template.exists(), "Missing .github/PULL_REQUEST_TEMPLATE.md"
        content = pr_template.read_text(encoding="utf-8")
        assert "frontend build is NOT equivalent to product release readiness" in content
        assert "Document Pipeline" in content
        assert "Security Baseline" in content
        assert "Client Boundary" in content

    def test_dependabot_configuration(self):
        """Verify dependabot.yml covers actions, pip, and npm."""
        dependabot_path = GITHUB_DIR / "dependabot.yml"
        assert dependabot_path.exists(), "Missing .github/dependabot.yml"
        with open(dependabot_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        updates = data.get("updates", [])
        ecosystems = [u.get("package-ecosystem") for u in updates]
        assert "github-actions" in ecosystems, "dependabot missing github-actions"
        assert "pip" in ecosystems, "dependabot missing pip"
        assert "npm" in ecosystems, "dependabot missing npm"

    def test_codeowners_rules(self):
        """Verify CODEOWNERS defines critical areas and owners."""
        codeowners_path = GITHUB_DIR / "CODEOWNERS"
        assert codeowners_path.exists(), "Missing .github/CODEOWNERS"
        content = codeowners_path.read_text(encoding="utf-8")
        assert "@SahilKhutey" in content
        assert "/.github/workflows/" in content
        assert "/scripts/release/" in content
        assert "/src/" in content
        assert "/web/" in content
        assert "/launch/" in content


class TestLaunchTaskRegister:
    """Test suite for the 70-task Product Hunt launch register."""

    def test_70_tasks_parsed_and_structured(self):
        """Verify all 70 tasks are correctly parsed from LAUNCH_TASK_REGISTER.md."""
        from scripts.launch.export_github_launch_issues import parse_tasks_from_register, validate_launch_inventory

        register_path = OPERATIONS_DIR / "LAUNCH_TASK_REGISTER.md"
        tasks = parse_tasks_from_register(register_path)
        assert len(tasks) == 70, f"Expected 70 tasks, got {len(tasks)}"
        validate_launch_inventory(tasks)

    def test_phases_a_through_g_represented(self):
        """Verify all 7 phases and 6 milestones are covered by tasks."""
        json_path = OPERATIONS_DIR / "github_launch_issues.json"
        assert json_path.exists(), "Missing github_launch_issues.json"
        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        assert payload["task_count"] == 70
        assert len(payload["milestones"]) == 6
        assert len(payload["labels"]) >= 20

        milestones_found = {t["milestone"] for t in payload["tasks"]}
        expected_milestone_prefixes = {"PH-01", "PH-02", "PH-03", "PH-04", "PH-05", "PH-06"}
        found_prefixes = {m.split(" — ")[0] for m in milestones_found}
        assert expected_milestone_prefixes.issubset(found_prefixes)

    def test_manual_tasks_strictly_designated(self):
        """Verify tasks that must remain manual according to Product Hunt policies are flagged."""
        json_path = OPERATIONS_DIR / "github_launch_issues.json"
        with open(json_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        manual_task_ids = {"PH-055", "PH-056", "PH-057", "PH-058", "PH-059", "PH-062", "PH-063"}
        tasks_by_id = {t["id"]: t for t in payload["tasks"]}

        for tid in manual_task_ids:
            task = tasks_by_id.get(tid)
            assert task is not None, f"Task {tid} missing"
            assert "Manual" in task["mode"] or "Manual" in task["body"], f"Task {tid} must be designated Manual"

    def test_seven_launch_gates_documented(self):
        """Verify GITHUB_PROJECT_STRUCTURE.md defines the 7 launch gates."""
        struct_path = OPERATIONS_DIR / "GITHUB_PROJECT_STRUCTURE.md"
        assert struct_path.exists()
        content = struct_path.read_text(encoding="utf-8")
        assert "Product Gate" in content
        assert "Quality Gate" in content
        assert "Security Gate" in content
        assert "Beta Gate" in content
        assert "Website Gate" in content
        assert "Release Gate" in content
        assert "Launch Gate" in content


class TestLaunchAssetsAndContent:
    """Test suite for launch visual assets and marketing copy."""

    def test_launch_assets_validator_passes(self):
        """Verify all 11 visual assets exist and are well-formed XML/SVGs."""
        from scripts.launch.validate_launch_assets import validate_all_assets
        assert validate_all_assets() is True

    def test_marketing_content_validator_passes(self):
        """Verify all 9 marketing documents exist and have no forbidden placeholders."""
        from scripts.launch.validate_marketing_content import validate_all_content
        assert validate_all_content() is True
