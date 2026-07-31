"""Entrypoint: `python -m amdi`."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

import structlog

from amdi.config import get_settings
from amdi.version import __version__

log = structlog.get_logger("amdi")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="amdi",
        description="AEGIS-DocIntel / AMDI-OS — Pre-LLM Document Intelligence OS",
    )
    p.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = p.add_subparsers(dest="cmd", required=False)

    sub.add_parser("serve", help="Run the FastAPI server (default)")
    sub.add_parser("info", help="Print runtime information")
    sub.add_parser("doctor", help="Diagnose environment readiness")

    return p


def _cmd_serve(args: argparse.Namespace) -> int:
    settings = get_settings()
    log.info(
        "amdi.serve.start",
        host=settings.api_host,
        port=settings.api_port,
        version=__version__,
    )
    try:
        import uvicorn
    except ImportError:
        print("ERROR: uvicorn not installed. Run: pip install 'uvicorn[standard]'", file=sys.stderr)
        return 1
    uvicorn.run(
        "amdi.api.app:create_app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        log_level=settings.api_log_level,
        factory=True,
    )
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    settings = get_settings()
    print(f"AEGIS-DocIntel / AMDI-OS  v{__version__}")
    print(f"Python     : {sys.version.split()[0]}")
    print(f"Storage    : {settings.storage_backend}  ->  {settings.storage_root}")
    print(f"Embeddings : {settings.embedding_model}")
    print(f"Token budget default: {settings.default_token_budget}")
    return 0



def _cmd_doctor(args: argparse.Namespace) -> int:
    """Report missing optional dependencies / misconfiguration."""
    issues: list[str] = []
    notes: list[str] = []

    try:
        import numpy  # noqa: F401
        notes.append("[OK] numpy")
    except ImportError:
        issues.append("[MISSING] numpy missing")

    try:
        import fitz  # PyMuPDF
        notes.append("[OK] pymupdf")
    except ImportError:
        issues.append("[MISSING] pymupdf missing - PDF ingest disabled")

    try:
        import pytesseract  # noqa: F401
        notes.append("[OK] tesseract wrapper present (system binary required)")
    except ImportError:
        notes.append("[OPTIONAL] tesseract wrapper not installed")

    settings = get_settings()
    if settings.jwt_secret.startswith("INSECURE-DEV"):
        issues.append("[WARN] JWT_SECRET is set to dev default - set AMDI_JWT_SECRET in production")

    print("\n".join(notes))
    if issues:
        print("\nIssues:")
        print("\n".join(f"  {i}" for i in issues))
        return 2
    print("\nEnvironment OK.")
    return 0



def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    cmd = args.cmd or "serve"

    if cmd == "serve":
        return _cmd_serve(args)
    if cmd == "info":
        return _cmd_info(args)
    if cmd == "doctor":
        return _cmd_doctor(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
