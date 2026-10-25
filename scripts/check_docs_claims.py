#!/usr/bin/env python3
"""
scripts/check_docs_claims.py — keep the docs truthful by machine, not by promise.

This repo's central failure mode (found repeatedly) was prose that asserted things nobody
re-checked: a README that said "944 tests passing" when the suite had grown past 1,060 and
the documented install path actually aborted with zero tests run; "verified" pilot case
studies when GitHub had zero issues; a security doc describing an env var (ALLOW_DEV_BYPASS)
that does not exist in the code. These rules make those classes of drift fail CI.

Rules
  R1  cold-start   Every command in scripts/cold_start_check.sh's README_COMMANDS block must
                   appear verbatim in README.md (the README *is* the tested path).
  R2  links        Relative markdown links in README/STATUS/docs resolve to real files, and
                   every mkdocs.yml nav target exists.
  R3  counts       No hard-coded test-pass counts ("944 passed", "1,030 tests passing") in
                   living docs. Counts rot; link to CI instead. (History files are exempt.)
  R4  pilots       Any quantified pilot / case-study claim must link a public GitHub issue on
                   the same line. No evidence, no claim.
  R5  readiness    "production-ready" may appear only when negated ("not production-ready").
  R6  env-vars     Every AEGIS_*/ALLOW_* style environment variable named in the docs must
                   exist in the code (src/, backend/, deploy/, Dockerfile, *.toml, workflows).

Usage:  python scripts/check_docs_claims.py          (exit 1 on any violation)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Living documents: held to every rule.
LIVING = ["README.md", "STATUS.md", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md"]
LIVING_GLOBS = ["docs/*.md", "docs/pilot/*.md"]
# Historical records: they describe what was claimed/true *at the time*; exempt from R3/R4/R5
# (R2 link checks still apply, R6 does not).
HISTORY = {"docs/DEVLOG.md", "docs/devlog.md", "docs/ROADMAP.md", "docs/MASTER_REMEDIATION_CHECKLIST.md",
           "CHANGELOG.md", "docs/changelog.md"}
ISSUE_URL = "github.com/SahilKhutey/AEGIS-DocIntel/issues/"

COUNT_RE = re.compile(r"\b\d[\d,]{2,}\+?\s+(?:unit\s+|passing\s+)?(?:tests?\s+)?(?:passed|passing|pass)\b", re.I)
PILOT_RE = re.compile(r"\bpilot|case[- ]stud", re.I)
QUANT_RE = re.compile(r"\d+(?:\.\d+)?\s*%|\btokens?\b|\bSSNs?\b|false[- ]positive", re.I)
READY_RE = re.compile(r"production[- ]ready", re.I)
NEGATED_RE = re.compile(r"\b(?:not|never|isn['’]t|no longer)\b[^.\n]{0,40}production[- ]ready", re.I)
# A line that RETRACTS the claim ("... status — removed", "previously claimed ...") is a correction, not a claim.
RETRACTED_RE = re.compile(r"\b(?:removed|retracted|withdrawn|previously (?:claimed|presented)|was claimed)\b", re.I)
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)\)")
# Mentioning a variable in order to say it does NOT exist is a correction, not a claim.
NONEXISTENT_RE = re.compile(r"does not exist|never existed|nonexistent|there is no `|no such (?:variable|env)", re.I)
ENV_RE = re.compile(r"\b((?:AEGIS|ALLOW)_[A-Z0-9_]{3,})\b")


def living_files() -> list[Path]:
    files = [ROOT / f for f in LIVING if (ROOT / f).exists()]
    for g in LIVING_GLOBS:
        files += sorted(ROOT.glob(g))
    return sorted(set(files))


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def strip_code_fences(text: str) -> list[tuple[int, str]]:
    """(lineno, line) for prose lines only, skipping fenced code blocks."""
    out, fenced = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def check_cold_start(problems: list[str]) -> None:
    script = (ROOT / "scripts" / "cold_start_check.sh").read_text(encoding="utf-8")
    m = re.search(r"README-COMMANDS-BEGIN\n(.*?)# README-COMMANDS-END", script, re.S)
    if not m:
        problems.append("R1 scripts/cold_start_check.sh: README-COMMANDS block not found")
        return
    cmds = re.findall(r'^\s*"([^"]+)"\s*$', m.group(1), re.M)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for c in cmds:
        if c not in readme:
            problems.append(f"R1 README.md does not contain the tested cold-start command verbatim: `{c}`")


def check_links(problems: list[str]) -> None:
    for f in living_files():
        for lineno, line in strip_code_fences(f.read_text(encoding="utf-8")):
            for target in LINK_RE.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path = target.split("#")[0]
                if path and not (f.parent / path).resolve().exists():
                    problems.append(f"R2 {rel(f)}:{lineno} broken link -> {target}")
    nav = ROOT / "mkdocs.yml"
    if nav.exists():
        for m in re.finditer(r":\s*([\w./\-]+\.md)\s*$", nav.read_text(encoding="utf-8"), re.M):
            if not (ROOT / "docs" / m.group(1)).exists():
                problems.append(f"R2 mkdocs.yml nav entry points to missing docs/{m.group(1)}")


def check_prose_rules(problems: list[str]) -> None:
    for f in living_files():
        name = rel(f)
        if name in HISTORY:
            continue
        for lineno, line in strip_code_fences(f.read_text(encoding="utf-8")):
            if COUNT_RE.search(line):
                problems.append(f"R3 {name}:{lineno} hard-coded test count (link CI instead): {line.strip()[:90]}")
            if PILOT_RE.search(line) and QUANT_RE.search(line) and ISSUE_URL not in line:
                problems.append(f"R4 {name}:{lineno} quantified pilot claim with no linked public issue: {line.strip()[:90]}")
            if READY_RE.search(line) and not (NEGATED_RE.search(line) or RETRACTED_RE.search(line)):
                problems.append(f"R5 {name}:{lineno} 'production-ready' used un-negated: {line.strip()[:90]}")


def check_env_vars(problems: list[str]) -> None:
    corpus = []
    for pattern in ("src/**/*.py", "backend/**/*.py", "deploy/**/*", "Dockerfile", "*.toml", "*.yml", ".github/**/*.yml", "scripts/*"):
        for p in ROOT.glob(pattern):
            # never let this checker's own docstring/examples count as evidence the code uses a variable
            if p.is_file() and "__pycache__" not in p.parts and p.name != Path(__file__).name:
                try:
                    corpus.append(p.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
    haystack = "\n".join(corpus)
    for f in living_files():
        name = rel(f)
        if name in HISTORY:
            continue
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if NONEXISTENT_RE.search(line):
                continue
            for var in ENV_RE.findall(line):
                if var not in haystack:
                    problems.append(f"R6 {name}:{lineno} documents env var {var} that does not exist in the code")


def main() -> int:
    problems: list[str] = []
    check_cold_start(problems)
    check_links(problems)
    check_prose_rules(problems)
    check_env_vars(problems)
    if problems:
        print(f"DOCS CLAIM CHECK FAILED — {len(problems)} violation(s):\n")
        for p in sorted(set(problems)):
            print("  ✗", p)
        return 1
    print("OK — docs claims check passed (R1 cold-start, R2 links, R3 counts, R4 pilots, R5 readiness, R6 env-vars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
