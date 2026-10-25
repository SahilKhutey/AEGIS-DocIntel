"""
Docs-as-tests: every ```python block in the user-facing docs is EXECUTED.

Why: the headline package's documented quickstart began with
``from aegis_docprep import RedactionEngine`` — a class that does not exist — and printed a
fictional ``[EMAIL_REDACTED]`` output for a detector that never recognised emails. Prose
review cannot catch that; running the example on the first line does.

Opt-out (for blocks needing optional frameworks or illustrating pseudo-code): put
``<!-- doc-test: skip reason="..." -->`` on the line immediately before the opening fence.
A skip must carry a reason; a bare skip is itself a test failure.

Documented OUTPUTS are verified too: after a ``# Output:`` line, the consecutive ``# ...``
comment lines are the claimed stdout. Each must appear, in order, in the real stdout. (The
PII example once documented a detected phone number and a fully-redacted name while the real
output left both in clear text — a privacy tool's own example leaking PII.)

Blocks run in a clean subprocess with ``aegis-docprep/`` on PYTHONPATH (what a source
install provides), so they cannot pass by accident via this repo's own ``src`` tree.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["aegis-docprep/README.md", "docs/docprep.md"]
SKIP_RE = re.compile(r'<!--\s*doc-test:\s*skip(?:\s+reason="([^"]+)")?\s*-->')


def extract_blocks(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```python"):
            start = i + 1
            prev = next((lines[j] for j in range(i - 1, -1, -1) if lines[j].strip()), "")
            j = start
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            yield start + 1, "\n".join(lines[start:j]), SKIP_RE.search(prev)
            i = j
        i += 1


def expected_output(code: str) -> list[str]:
    """Lines claimed as stdout: the '# ...' comment run following each '# Output:' marker."""
    lines, claimed, i = code.splitlines(), [], 0
    while i < len(lines):
        if re.match(r"\s*#\s*Output:?\s*$", lines[i], re.I):
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("#"):
                claimed.append(re.sub(r"^\s*#\s?", "", lines[i]).rstrip())
                i += 1
            continue
        i += 1
    return [c for c in claimed if c.strip()]


CASES = [
    pytest.param(doc, lineno, code, skip, id=f"{doc}:{lineno}")
    for doc in DOCS
    if (ROOT / doc).exists()
    for lineno, code, skip in extract_blocks(ROOT / doc)
]


def test_docs_have_runnable_examples():
    assert CASES, "no python blocks found — extraction is broken, or the docs lost their examples"


@pytest.mark.parametrize("doc, lineno, code, skip", CASES)
def test_documented_example_runs(doc, lineno, code, skip):
    if skip:
        assert skip.group(1), f"{doc}:{lineno}: a doc-test skip must state a reason"
        pytest.skip(skip.group(1))
    env = {**os.environ, "PYTHONPATH": str(ROOT / "aegis-docprep"), "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        cwd=ROOT / "aegis-docprep", env=env, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, (
        f"{doc}:{lineno} — documented example FAILS:\n{proc.stderr.strip().splitlines()[-1] if proc.stderr else ''}\n"
        f"--- code ---\n{code}"
    )
    # Documented output must be real: every claimed line appears, in order, in actual stdout.
    actual = [ln.rstrip() for ln in proc.stdout.splitlines()]
    pos = 0
    for claim in expected_output(code):
        try:
            pos = actual.index(claim, pos) + 1
        except ValueError:
            pytest.fail(
                f"{doc}:{lineno} — documented output does not match reality.\n"
                f"  claimed : {claim!r}\n  actual  :\n    " + "\n    ".join(actual)
            )
