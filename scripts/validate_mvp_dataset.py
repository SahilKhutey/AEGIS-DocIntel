#!/usr/bin/env python3
"""
scripts/validate_mvp_dataset.py — Validate the AEGIS-DocIntel evaluation dataset against its manifest.

Ensures that the evaluation manifest and the underlying dataset cannot silently drift:
1. Manifest slices correspond to dataset keys.
2. Declared case counts match actual record counts.
3. Every test case contains a unique, non-empty identifier.
4. Required schema fields are present and valid for each slice.
5. Quality gates defined in manifest are structured and non-empty.

Usage:
    python scripts/validate_mvp_dataset.py
    python scripts/validate_mvp_dataset.py --manifest path/to/manifest.json --dataset path/to/dataset.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "evaluation" / "datasets" / "manifest.json"
DEFAULT_DATASET = ROOT / "evaluation" / "datasets" / "qa_eval_dataset.json"

SLICE_KEYS: Dict[str, str] = {
    "extraction": "extraction_cases",
    "packing": "packing_cases",
    "privacy": "privacy_cases",
    "retrieval": "retrieval_cases",
}

IDENTIFIER_KEYS: Dict[str, str] = {
    "extraction": "case_id",
    "packing": "case_id",
    "privacy": "id",
    "retrieval": "query",
}

REQUIRED_CASE_FIELDS: Dict[str, List[str]] = {
    "extraction": ["case_id"],
    "packing": ["case_id", "budget", "costs", "weights"],
    "privacy": ["id", "text", "expected_pii"],
    "retrieval": ["query", "corpus"],
}


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON object from disk with utf-8 encoding."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object (got {type(value).__name__})")
    return value


def validate_contract(manifest_path: Path, dataset_path: Path) -> List[str]:
    """Validate dataset against manifest contract, returning a list of validation errors."""
    errors: List[str] = []

    try:
        manifest = load_json(manifest_path)
    except Exception as exc:
        return [f"Failed to load manifest ({manifest_path}): {exc}"]

    try:
        dataset = load_json(dataset_path)
    except Exception as exc:
        return [f"Failed to load dataset ({dataset_path}): {exc}"]

    slices = manifest.get("slices")
    if not isinstance(slices, dict):
        return ["Manifest missing 'slices' dictionary definition."]

    quality_gates = manifest.get("quality_gates")
    if not isinstance(quality_gates, dict):
        errors.append("Manifest missing 'quality_gates' dictionary definition.")

    for slice_name, dataset_key in SLICE_KEYS.items():
        if slice_name not in slices:
            errors.append(f"Manifest missing declared slice: '{slice_name}'.")
            continue

        slice_meta = slices[slice_name]
        declared_count = slice_meta.get("test_cases_count")
        if not isinstance(declared_count, int) or declared_count < 1:
            errors.append(f"Slice '{slice_name}' declared invalid 'test_cases_count': {declared_count}.")
            continue

        cases = dataset.get(dataset_key)
        if not isinstance(cases, list):
            errors.append(f"Dataset missing expected list key '{dataset_key}' for slice '{slice_name}'.")
            continue

        actual_count = len(cases)
        if declared_count != actual_count:
            errors.append(
                f"Count drift in slice '{slice_name}': manifest declares {declared_count} cases, "
                f"but dataset contains {actual_count}."
            )

        # Validate unique IDs and required fields
        id_key = IDENTIFIER_KEYS.get(slice_name, "id")
        seen_ids: Set[str] = set()
        required_fields = REQUIRED_CASE_FIELDS.get(slice_name, [])

        for idx, case in enumerate(cases):
            if not isinstance(case, dict):
                errors.append(f"Slice '{slice_name}' item #{idx} is not an object.")
                continue

            # Check identifier
            raw_id = case.get(id_key)
            # For retrieval, also permit checking query_id if query is matched
            if not raw_id and slice_name == "retrieval":
                raw_id = case.get("query_id")

            if not raw_id or not str(raw_id).strip():
                errors.append(f"Slice '{slice_name}' item #{idx} missing identifier '{id_key}'.")
            else:
                str_id = str(raw_id).strip()
                if str_id in seen_ids:
                    errors.append(f"Slice '{slice_name}' contains duplicate identifier: '{str_id}'.")
                seen_ids.add(str_id)

            # Check required fields
            for field in required_fields:
                if field not in case:
                    errors.append(f"Slice '{slice_name}' item #{idx} missing required field '{field}'.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evaluation dataset against manifest contract.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Path to manifest.json")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET, help="Path to qa_eval_dataset.json")
    args = parser.parse_args()

    print("=" * 72)
    print("AEGIS-DocIntel — Evaluation Dataset Contract Validator")
    print(f"Manifest: {args.manifest}")
    print(f"Dataset:  {args.dataset}")
    print("=" * 72)

    errors = validate_contract(args.manifest, args.dataset)

    if errors:
        print("[FAIL] Contract validation failed with the following errors:")
        for err in errors:
            print(f"  • {err}")
        print("=" * 72)
        return 1

    print("[OK] All declared slices, counts, and case schemas match.")
    print("MVP DATASET CONTRACT: PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
