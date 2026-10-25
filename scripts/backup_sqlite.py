from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def backup_database(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(f"Database not found: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    # Do not overwrite an existing backup by accident.
    if destination.exists():
        raise FileExistsError(f"Backup already exists: {destination}")

    src_conn = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    dst_conn = sqlite3.connect(str(destination.resolve()))
    try:
        src_conn.backup(dst_conn)
        result = dst_conn.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"Backup integrity check failed: {result}")
    except Exception:
        dst_conn.close()
        src_conn.close()
        destination.unlink(missing_ok=True)
        raise
    else:
        dst_conn.close()
        src_conn.close()

    # Best-effort local permission tightening; storage-level controls still matter.
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="AEGIS-DocIntel SQLite Online Backup Utility")
    parser.add_argument("source", type=Path, help="Path to source SQLite database")
    parser.add_argument("destination", type=Path, help="Path to destination backup file")
    args = parser.parse_args()

    try:
        backup_database(args.source, args.destination)
        print(f"Backup completed successfully: {args.destination}")
        return 0
    except Exception as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
