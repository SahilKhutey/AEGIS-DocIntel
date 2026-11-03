"""
aegis.evaluation.manifest.loader
================================
Loads and parses manifest files from YAML or JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union
import yaml

from .models import EvaluationManifest
from .validator import ManifestValidationError, ManifestValidator


class ManifestLoader:
    """Loads, validates, and initializes evaluation manifests."""

    @classmethod
    def load(
        cls,
        manifest_path: Union[str, Path],
        repo_root: Path | None = None,
        verify_integrity: bool = True,
    ) -> EvaluationManifest:
        path = Path(manifest_path)
        if not path.is_absolute() and repo_root:
            path = repo_root / path

        if not path.exists():
            raise FileNotFoundError(f"Manifest not found at {path}")

        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in [".yaml", ".yml"]:
                raw_data = yaml.safe_load(f)
            elif path.suffix == ".json":
                raw_data = json.load(f)
            else:
                raise ValueError(f"Unsupported manifest format '{path.suffix}'. Use .yaml or .json")

        manifest = EvaluationManifest(**raw_data)

        if verify_integrity:
            root = repo_root or path.parent.parent.parent
            valid, errors = ManifestValidator.validate_manifest(manifest, root)
            if not valid:
                raise ManifestValidationError(
                    f"Manifest validation failed with {len(errors)} error(s):\n"
                    + "\n".join(f"- {e}" for e in errors)
                )

        return manifest
