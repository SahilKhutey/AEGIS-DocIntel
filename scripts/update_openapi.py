from __future__ import annotations

import json
from pathlib import Path

from src.main import app


def generate_openapi() -> None:
    """Write the current FastAPI schema to the checked-in OpenAPI file."""
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / "openapi.json"
    with target.open("w", encoding="utf-8") as fh:
        json.dump(app.openapi(), fh, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    generate_openapi()
