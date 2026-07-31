"""Weekly digest generator (Markdown) for the #release channel.

Combines sweep_aggregate output + TRIAGE_LOG + (optional) METRICS_SUMMARY.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week-start", help="ISO date (Mon)")
    args = ap.parse_args()
    week = (dt.datetime.strptime(args.week_start, "%Y-%m-%d").date()
            if args.week_start
            else dt.date.today() - dt.timedelta(days=dt.date.today().weekday()))
    out_path = ROOT / f"release/v0.3.0-week1/DIGEST_{week.isoformat()}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parts = [f"# Weekly digest — week of {week.isoformat()}\n"]
    sweeps = ROOT / f"release/v0.3.0-week1/SWEEPS_{week.isoformat()}.md"
    if sweeps.exists():
        parts.append(sweeps.read_text(encoding="utf-8"))
    parts.append("## Triage\n")
    triage = ROOT / "release/v0.3.0-week1/TRIAGE_LOG.md"
    if triage.exists():
        parts.append(triage.read_text(encoding="utf-8"))
    parts.append("## Decisions\n")
    decisions = ROOT / "release/v0.3.0-week1/DECISIONS.md"
    if decisions.exists():
        parts.append(decisions.read_text(encoding="utf-8"))
    out_path.write_text("\n".join(parts), encoding="utf-8")
    print(out_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
