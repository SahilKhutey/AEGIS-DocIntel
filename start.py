#!/usr/bin/env python3
"""
AEGIS-DocIntel — Quick Start Script
=====================================
Run this to install dependencies and start the server.
"""
import os
import subprocess
import sys


def run(cmd: str, **kwargs):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(result.returncode)
    return result


def main():
    print("=" * 60)
    print("  AEGIS-DocIntel — Document Intelligence Platform")
    print("  Starting up...")
    print("=" * 60)

    # Install dependencies
    print("\n[1/3] Installing dependencies...")
    run(f"{sys.executable} -m pip install -r requirements.txt -q")

    # Set development environment
    os.environ.setdefault("OPENAI_API_KEY", "")
    os.environ.setdefault("S3_ENDPOINT", "http://localhost:9000")
    os.environ.setdefault("S3_ACCESS_KEY", "minioadmin")
    os.environ.setdefault("S3_SECRET_KEY", "minioadmin")

    print("\n[2/3] Running quick tests...")
    test_result = subprocess.run(
        f"{sys.executable} -m pytest tests/test_aegis.py::TestHealth tests/test_aegis.py::TestConfiguration -v --tb=short",
        shell=True
    )

    print("\n[3/3] Starting AEGIS-DocIntel API server...")
    print("\n" + "=" * 60)
    print("  API:     http://localhost:8000")
    print("  Docs:    http://localhost:8000/docs")
    print("  Metrics: http://localhost:9090")
    print("  Health:  http://localhost:8000/health")
    print("=" * 60)
    print("\n  Test with:")
    print("  curl -H 'X-API-Key: aegis-dev-key' http://localhost:8000/health")
    print("\n  Upload a PDF:")
    print("  curl -X POST http://localhost:8000/v1/documents/upload \\")
    print("       -H 'X-API-Key: aegis-dev-key' \\")
    print("       -F 'file=@your_document.pdf'")
    print("\n  Query:")
    print("  curl -X POST http://localhost:8000/v1/query \\")
    print("       -H 'X-API-Key: aegis-dev-key' \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"question\": \"What is this document about?\"}'")
    print("=" * 60 + "\n")

    run(
        f"{sys.executable} -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload",
        cwd=os.path.dirname(os.path.abspath(__file__))
    )


if __name__ == "__main__":
    main()
