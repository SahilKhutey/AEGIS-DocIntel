"""
aegis/audit/__main__.py
=======================
CLI entry point for the AEGIS unified audit infrastructure.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from aegis.audit.config.loader import AuditConfigLoader
from aegis.audit.config.validator import AuditConfigValidator
from aegis.audit.evidence.store import EvidenceStore
from aegis.audit.runner.engine import AuditRunner
from aegis.audit.runner.planner import AuditPlanner
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.traceability.historical_comparison import HistoricalComparison


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m aegis.audit",
        description="AEGIS-DocIntel Unified Audit Infrastructure CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Audit subcommands")

    # list
    subparsers.add_parser("list", help="List registered audit suites")

    # validate
    val_p = subparsers.add_parser("validate", help="Validate audit configuration contract")
    val_p.add_argument("--config", "-c", type=str, default="configs/audit/default.yaml", help="Path to config file")

    # plan
    plan_p = subparsers.add_parser("plan", help="Preview execution plan without running")
    plan_p.add_argument("--config", "-c", type=str, default="configs/audit/default.yaml")
    plan_p.add_argument("--suite", "-s", action="append", help="Specific suite ID to plan")
    plan_p.add_argument("--all", action="store_true", help="Plan all registered suites")

    # run
    run_p = subparsers.add_parser("run", help="Execute audit suites")
    run_p.add_argument("--config", "-c", type=str, default="configs/audit/default.yaml")
    run_p.add_argument("--suite", "-s", action="append", help="Specific suite ID to run")
    run_p.add_argument("--all", action="store_true", help="Execute all eligible suites")
    run_p.add_argument("--dry-run", action="store_true", help="Simulate run without execution")

    # inspect
    insp_p = subparsers.add_parser("inspect", help="Inspect a previous audit run")
    insp_p.add_argument("run_id", type=str, help="Audit run identifier (e.g. AG-20261103-...)")

    # verify
    ver_p = subparsers.add_parser("verify", help="Verify evidence integrity and hashes of a run")
    ver_p.add_argument("run_id", type=str, help="Audit run identifier")

    # compare
    cmp_p = subparsers.add_parser("compare", help="Compare two historical audit runs")
    cmp_p.add_argument("run_a", type=str, help="Baseline run identifier")
    cmp_p.add_argument("run_b", type=str, help="Current run identifier")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "list":
            runner = AuditRunner()
            suites = runner.registry.list_suites()
            print(f"Registered Audit Suites ({len(suites)}):")
            for sid in suites:
                s = runner.registry.get(sid)
                print(f"  - {s.suite_id.ljust(15)} : {s.suite_name} (v{s.suite_version})")
            return 0

        elif args.command == "validate":
            config = AuditConfigLoader.load(args.config)
            runner = AuditRunner(config=config)
            res = runner.validate_configuration()
            print(json.dumps(res, indent=2))
            return 0 if res["configuration_status"] == "VALID" else 1

        elif args.command == "plan":
            config = AuditConfigLoader.load(args.config)
            runner = AuditRunner(config=config)
            res = runner.run(suite_ids=args.suite, all_suites=args.all, dry_run=True)
            print(f"Execution Plan ({res['planned_suites_count']} suites):")
            for sid in res["planned_suites"]:
                print(f"  - {sid}")
            print(f"Configuration Fingerprint: {res['configuration_hash']}")
            return 0

        elif args.command == "run":
            profile_name = Path(args.config).stem
            runner = AuditRunner(config_path=args.config)
            res = runner.run(
                suite_ids=args.suite,
                all_suites=args.all,
                dry_run=args.dry_run,
                profile_name=profile_name,
            )
            print(res.get("markdown", json.dumps(res, indent=2)))
            status = res.get("status")
            return 0 if status in {"PASSED", "DRY_RUN"} else 1

        elif args.command == "inspect":
            store = EvidenceStore()
            run_data = store.get_run(args.run_id)
            if not run_data:
                print(f"[ERROR] Run not found: {args.run_id}", file=sys.stderr)
                return 1
            print(json.dumps(run_data, indent=2))
            return 0

        elif args.command == "verify":
            store = EvidenceStore()
            ver_res = store.verify_integrity(args.run_id)
            print(json.dumps(ver_res, indent=2))
            return 0 if ver_res["status"] == "PASS" else 1

        elif args.command == "compare":
            store = EvidenceStore()
            run_a = store.get_run(args.run_a)
            run_b = store.get_run(args.run_b)
            if not run_a or not run_b:
                print(f"[ERROR] One or both runs not found for comparison", file=sys.stderr)
                return 1
            diff = HistoricalComparison.compare(run_a, run_b)
            print(json.dumps(diff, indent=2))
            return 0

        return 0

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
