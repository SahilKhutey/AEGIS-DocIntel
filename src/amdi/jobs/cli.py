"""Convenience CLI: amdi-worker run | amdi-worker prune."""

from __future__ import annotations

import argparse
import asyncio
import sys

from arq.cli import main as arq_main  # type: ignore

from amdi.config import get_settings
from amdi.jobs.ledger import make_ledger


def _prune() -> int:
    async def _run() -> int:
        return await make_ledger().prune(get_settings().job_keep_results_s)
    return asyncio.run(_run())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="amdi-worker")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run", help="Run the arq worker")
    sub.add_parser("prune", help="Drop old job ledgers")

    args = p.parse_args(argv)
    if args.cmd == "run":
        # Re-export arq's CLI: arq <settings module>
        sys.argv = ["arq", "amdi.jobs.worker.WorkerSettings"]
        return arq_main()
    if args.cmd == "prune":
        removed = _prune()
        print(f"pruned {removed} ledger entries")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
