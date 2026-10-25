"""Docs may not drift from reality: see scripts/check_docs_claims.py for rules R1-R6."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_docs_claims_check_passes():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_docs_claims.py")],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout
