"""Heuristic issue triage: take a webhook payload -> assign labels + severity.

The script reads JSON from stdin shaped like:

  { "title": "...", "body": "...", "labels": [] }

and prints the assigned labels.
"""

from __future__ import annotations

import json
import re
import sys


COMPONENT_PATTERNS = {
    "K-perf":        r"\b(slow|perf|latency|memory|leak|timeout)\b",
    "K-sdk":         r"\b(sdk|proto|grpc)\b",
    "K-ui":          r"\b(react|streamlit|ui|dashboard|frontend)\b",
    "K-deprecation": r"\b(legacy_bridge|deprecated)\b",
    "K-obs":         r"\b(prometheus|grafana|metric|trace)\b",
    "K-policy":      r"\b(sla|security|policy|license)\b",
    "K-bot":         r"\b(dependabot|bot/sweep|github-actions)\b",
    "K-research":    r"\b(topology|tensor|spectral|homology)\b",
    "K-stable":      r"\b(api|schema|contract|wire)\b",
}

SEVERITY_WORDS = {
    "Sev-1": r"\b(outage|data loss|security|cve|rce|exploit)\b",
    "Sev-2": r"\b(breaks|crash|hang|broken|regression)\b",
    "Sev-3": r"\b(typo|cosmetic|small|minor|nit)\b",
}


def main() -> int:
    payload = json.load(sys.stdin)
    text = " ".join([payload.get("title", ""), payload.get("body", "")]).lower()
    labels = [k for k, rx in COMPONENT_PATTERNS.items() if re.search(rx, text)]
    sev = next((s for s, rx in SEVERITY_WORDS.items() if re.search(rx, text)),
                "Sev-3")
    print(json.dumps({"labels": labels, "severity": sev}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())