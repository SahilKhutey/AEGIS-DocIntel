"""Weekly aggregator for the four sweep bots.

Each nightly sweep writes a JSON file to .amdi_data/sweeps/. We
aggregate by week and emit a single markdown summary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SWEEPS = ROOT / ".amdi_data" / "sweeps"


def load_week(week_start: dt.date) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"drift": [], "openapi_sync": [],
                                   "audit_integrity": [], "deps": []}
    if not SWEEPS.exists():
        return out
    for f in sorted(SWEEPS.glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        ts_str = rec.get("ts", "")
        if not ts_str:
            continue
        try:
            d = dt.datetime.fromisoformat(ts_str).date()
        except ValueError:
            continue
        if d < week_start or d >= week_start + dt.timedelta(days=7):
            continue
        kind = rec.get("kind")
        if kind in out:
            out[kind].append(rec)
    return out


def render_md(week: dict[str, list[dict]]) -> str:
    md = ["# Weekly sweep aggregate\n"]
    for kind, recs in week.items():
        ok = sum(1 for r in recs if r.get("ok"))
        bad = len(recs) - ok
        md.append(f"## {kind}")
        md.append(f"- runs: {len(recs)} · ok: {ok} · failed: {bad}")
        if bad:
            offenders = Counter(r.get("offender", "?") for r in recs if not r.get("ok"))
            for offender, n in offenders.most_common(5):
                md.append(f"  - `{offender}` x{n}")
        md.append("")
    return "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week-start", help="ISO date (Mon). Default: this week's Mon.")
    args = ap.parse_args()
    week_start = (dt.datetime.strptime(args.week_start, "%Y-%m-%d").date()
                  if args.week_start
                  else dt.date.today() - dt.timedelta(days=dt.date.today().weekday()))
    week = load_week(week_start)
    out = ROOT / f"release/v0.3.0-week1/SWEEPS_{week_start.isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_md(week), encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())