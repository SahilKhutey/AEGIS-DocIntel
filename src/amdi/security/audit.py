"""Hash-chained audit log."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger("amdi.security.audit")


@dataclass
class AuditRecord:
    ts: int
    actor: str
    action: str
    resource: str
    outcome: str
    code: str = ""
    detail: str = ""
    prev_hash: str = "0" * 64
    hash: str = field(default="", init=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("hash", None)
        return d


class AuditChain:
    """Append-only hash-chained log."""

    def __init__(self, *, backend: str = "file",
                 root: Path | None = None,
                 sink_path: Path | None = None) -> None:
        self.backend = backend
        self._lock_path: Path | None = None
        self._prev_hash = "0" * 64

        if backend == "file":
            base = sink_path or (root or Path(".amdi_data")) / "audit"
            base.mkdir(parents=True, exist_ok=True)
            self._lock_path = base / ".lock"
            latest = max(base.glob("audit-*.log"), default=None)
            if latest:
                last_line = latest.read_text(encoding="utf-8").strip().splitlines()[-1]
                try:
                    rec = json.loads(last_line)
                    self._prev_hash = rec.get("hash", self._prev_hash)
                except Exception:  # noqa: BLE001
                    pass

    def append(self, rec: AuditRecord) -> AuditRecord:
        rec.prev_hash = self._prev_hash
        blob = json.dumps(rec.to_dict(), sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        rec.hash = h
        self._prev_hash = h

        line = json.dumps({**asdict(rec)}, separators=(",", ":"))

        if self.backend == "file":
            from datetime import datetime, timezone
            fname = f"audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
            target = self._lock_path.parent / fname  # type: ignore[union-attr]
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        elif self.backend == "stdout":
            print(line, flush=True)
        else:
            raise ValueError(f"unknown audit backend: {self.backend}")

        return rec


def verify_file(path: Path) -> tuple[bool, int]:
    """Replay an audit log; return (ok, records_checked)."""
    prev = "0" * 64
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        expected_prev = rec.get("prev_hash", "?")
        h = rec.pop("hash", "")
        blob = json.dumps(rec, sort_keys=True, separators=(",", ":"))
        actual = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        if expected_prev != prev or actual != h:
            return False, n
        prev = h
        n += 1
    return True, n



__all__ = ["AuditRecord", "AuditChain", "verify_file"]
