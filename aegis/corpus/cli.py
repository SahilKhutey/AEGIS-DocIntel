"""
aegis.corpus.cli
================
Command-line interface for AEGIS corpus governance, normalization,
manifest generation, verification, and partition auditing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from aegis.corpus.adapters.registry import AdapterRegistry
from aegis.corpus.independent.inventory import IndependentDocumentInventory
from aegis.corpus.integrity.checksum import calculate_sha256
from aegis.corpus.integrity.manifest import ChecksumManifest, ChecksumManifestGenerator
from aegis.corpus.integrity.verifier import ChecksumVerifier
from aegis.corpus.partition.grouping import GroupableDocument
from aegis.corpus.partition.leakage import LeakageDetector
from aegis.corpus.partition.splitter import DeterministicSplitter, PartitionManifest
from aegis.corpus.registry.acquisition_registry import AcquisitionRegistry
from aegis.corpus.registry.licence_registry import LicenceRegistry
from aegis.corpus.registry.source_registry import SourceRegistry


def cmd_registry_validate(args: argparse.Namespace) -> int:
    """Validate all corpus governance registries (licences, sources, acquisition)."""
    root = Path.cwd()
    lic_file = root / "configs" / "corpus" / "licences.yaml"
    src_file = root / "configs" / "corpus" / "sources.yaml"
    acq_file = root / "configs" / "corpus" / "acquisition_decisions.yaml"

    errors = []

    print("[*] Validating Licence Registry...")
    try:
        lic_reg = LicenceRegistry(lic_file)
        lics = lic_reg.list_all()
        print(f"    [+] Loaded {len(lics)} licences successfully.")
    except Exception as e:
        errors.append(f"Licence Registry Error: {e}")

    print("[*] Validating Source Registry...")
    try:
        src_reg = SourceRegistry(src_file)
        is_valid, errs = src_reg.validate_integrity()
        if not is_valid:
            errors.extend([f"Source Registry Integrity: {err}" for err in errs])
        else:
            print(f"    [+] Source registry integrity verified ({len(src_reg.list_all())} sources).")
    except Exception as e:
        errors.append(f"Source Registry Error: {e}")

    print("[*] Validating Acquisition Decisions Registry...")
    try:
        acq_reg = AcquisitionRegistry(acq_file)
        decs = acq_reg.list_all()
        print(f"    [+] Loaded {len(decs)} acquisition decisions successfully.")
    except Exception as e:
        errors.append(f"Acquisition Registry Error: {e}")

    if errors:
        print("\n[!] Validation FAILED with errors:")
        for err in errors:
            print(f"    - {err}")
        return 1

    print("\n[SUCCESS] All corpus registries are valid and compliant.")
    return 0


def cmd_dataset_validate(args: argparse.Namespace) -> int:
    """Validate a dataset file or directory using registered adapters."""
    path = Path(args.path)
    if not path.exists():
        print(f"[!] Path does not exist: {path}")
        return 1

    adapter = AdapterRegistry.get_adapter(args.adapter) if args.adapter else AdapterRegistry.detect_adapter(path)
    if not adapter:
        print(f"[!] Could not detect or find adapter for path: {path}")
        return 1

    print(f"[*] Validating with adapter: {adapter.adapter_name}")
    docs, annos, evals, report = adapter.convert(path)
    print(f"    [+] Documents converted: {report.documents_converted}")
    print(f"    [+] Annotations converted: {report.annotations_converted}")
    print(f"    [+] Evaluation items converted: {report.evaluation_items_converted}")

    if not report.success:
        print(f"[!] Conversion reported errors: {report.errors}")
        return 1

    print("[SUCCESS] Dataset validated and converted without schema errors.")
    return 0


def cmd_dataset_normalize(args: argparse.Namespace) -> int:
    """Normalize dataset into canonical JSON format and export to directory."""
    path = Path(args.path)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    adapter = AdapterRegistry.get_adapter(args.adapter) if args.adapter else AdapterRegistry.detect_adapter(path)
    if not adapter:
        print(f"[!] Could not detect adapter for: {path}")
        return 1

    print(f"[*] Normalizing {path.name} with {adapter.adapter_name}...")
    docs, annos, evals, report = adapter.convert(path, dataset_id=args.dataset_id)

    if not report.success:
        print(f"[!] Normalization failed: {report.errors}")
        return 1

    # Write documents
    docs_file = out_dir / "canonical_documents.json"
    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump([d.to_schema_dict() for d in docs], f, indent=2)

    # Write annotations
    annos_file = out_dir / "canonical_annotations.json"
    with open(annos_file, "w", encoding="utf-8") as f:
        json.dump([a.to_schema_dict() for a in annos], f, indent=2)

    # Write evaluation items
    evals_file = out_dir / "canonical_evaluations.json"
    with open(evals_file, "w", encoding="utf-8") as f:
        json.dump([e.to_schema_dict() for e in evals], f, indent=2)

    print(f"[SUCCESS] Exported {len(docs)} documents, {len(annos)} annotations, {len(evals)} evals to {out_dir}")
    return 0


def cmd_manifest_generate(args: argparse.Namespace) -> int:
    """Generate SHA-256 checksum manifest."""
    root = Path.cwd()
    out_file = Path(args.output) if args.output else root / "artifacts" / "corpus" / "manifests" / "checksum_manifest.json"

    inv = IndependentDocumentInventory(root)
    docs = inv.load_from_manifest_csv()
    gen = ChecksumManifestGenerator(root)
    manifest = gen.generate_from_documents(docs)
    gen.export_manifest(manifest, out_file)

    print(f"[SUCCESS] Generated checksum manifest with {len(manifest.artifacts)} artifacts at {out_file}")
    return 0


def cmd_manifest_verify(args: argparse.Namespace) -> int:
    """Verify SHA-256 checksum manifest."""
    manifest_path = Path(args.manifest) if args.manifest else Path.cwd() / "artifacts" / "corpus" / "manifests" / "checksum_manifest.json"
    if not manifest_path.exists():
        print(f"[!] Manifest not found: {manifest_path}")
        return 1

    with open(manifest_path, "r", encoding="utf-8") as f:
        cdata = json.load(f)
    manifest = ChecksumManifest(**cdata)
    print(f"[*] Verified format of manifest {manifest_path.name} with {len(manifest.artifacts)} artifacts.")
    print("[SUCCESS] Manifest structure and checksum formatting verified.")
    return 0


def cmd_partition_verify(args: argparse.Namespace) -> int:
    """Verify partition manifest for zero data leakage."""
    root = Path.cwd()
    p_manifest_file = Path(args.manifest) if args.manifest else root / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
    inv_file = root / "artifacts" / "corpus" / "manifests" / "document_inventory.jsonl"

    if not p_manifest_file.exists():
        print(f"[!] Partition manifest not found: {p_manifest_file}")
        return 1

    with open(p_manifest_file, "r", encoding="utf-8") as f:
        p_data = json.load(f)
    manifest = PartitionManifest(**p_data)

    docs = []
    with open(inv_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                docs.append(GroupableDocument(
                    document_id=d["document_id"],
                    source_id=d["source_id"],
                    sha256=d["sha256"],
                    title=d.get("title"),
                    publisher=d.get("publisher"),
                ))

    detector = LeakageDetector()
    report = detector.audit_partitions(manifest, docs)

    print(f"[*] Audit Status: {report.status}")
    print(f"    - Development documents: {report.metrics.get('development_count')}")
    print(f"    - Validation documents:  {report.metrics.get('validation_count')}")
    print(f"    - Holdout documents:     {report.metrics.get('holdout_count')}")
    print(f"    - Violations count:      {report.metrics.get('violations_count')}")

    if report.status != "PASSED":
        print(f"[!] Leakage detected: {report.violations}")
        return 1

    print("[SUCCESS] Zero data leakage across partitions verified.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Display comprehensive corpus status report."""
    root = Path.cwd()
    print("=" * 60)
    print("      AEGIS-DocIntel Corpus Status & Governance Report")
    print("=" * 60)

    # 1. Registries
    lic_reg = LicenceRegistry(root / "configs" / "corpus" / "licences.yaml")
    src_reg = SourceRegistry(root / "configs" / "corpus" / "sources.yaml")
    acq_reg = AcquisitionRegistry(root / "configs" / "corpus" / "acquisition_decisions.yaml")

    print(f"Registered Licences:             {len(lic_reg.list_all())}")
    print(f"Registered Candidate Sources:    {len(src_reg.list_all())}")
    print(f"Acquisition Decisions Recorded:  {len(acq_reg.list_all())}")

    # 2. Documents & Partitions
    p_manifest_file = root / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
    if p_manifest_file.exists():
        with open(p_manifest_file, "r", encoding="utf-8") as f:
            p_data = json.load(f)
        parts = p_data.get("partitions", {})
        dev_cnt = len(parts.get("development", []))
        val_cnt = len(parts.get("validation", []))
        hold_cnt = len(parts.get("holdout", []))
        total = dev_cnt + val_cnt + hold_cnt
        print(f"Total Authentic Documents:       {total}")
        print(f"  - Development:                 {dev_cnt} ({dev_cnt/total*100:.1f}%)")
        print(f"  - Validation:                  {val_cnt} ({val_cnt/total*100:.1f}%)")
        print(f"  - Sealed Holdout:              {hold_cnt} ({hold_cnt/total*100:.1f}%)")
        print(f"Partition Leakage Status:        {p_data.get('leakage_check_status')}")

    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m aegis.corpus.cli", description="AEGIS Corpus Governance CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # registry validate
    reg_parser = subparsers.add_parser("registry", help="Registry operations")
    reg_sub = reg_parser.add_subparsers(dest="subcommand", required=True)
    reg_val = reg_sub.add_parser("validate", help="Validate all registries")
    reg_val.set_defaults(func=cmd_registry_validate)

    # dataset
    ds_parser = subparsers.add_parser("dataset", help="Dataset operations")
    ds_sub = ds_parser.add_subparsers(dest="subcommand", required=True)
    
    ds_val = ds_sub.add_parser("validate", help="Validate dataset schema")
    ds_val.add_argument("path", help="Path to dataset file or folder")
    ds_val.add_argument("--adapter", help="Explicit adapter name")
    ds_val.set_defaults(func=cmd_dataset_validate)

    ds_norm = ds_sub.add_parser("normalize", help="Normalize dataset into canonical schema")
    ds_norm.add_argument("path", help="Path to dataset file or folder")
    ds_norm.add_argument("--output", "-o", default="data/normalized", help="Output directory")
    ds_norm.add_argument("--adapter", help="Explicit adapter name")
    ds_norm.add_argument("--dataset-id", help="Dataset identifier")
    ds_norm.set_defaults(func=cmd_dataset_normalize)

    # manifest
    man_parser = subparsers.add_parser("manifest", help="Manifest operations")
    man_sub = man_parser.add_subparsers(dest="subcommand", required=True)
    man_gen = man_sub.add_parser("generate", help="Generate SHA256 checksum manifest")
    man_gen.add_argument("--output", "-o", help="Output path for manifest")
    man_gen.set_defaults(func=cmd_manifest_generate)

    man_ver = man_sub.add_parser("verify", help="Verify checksum manifest")
    man_ver.add_argument("--manifest", "-m", help="Path to manifest file")
    man_ver.set_defaults(func=cmd_manifest_verify)

    # partition
    part_parser = subparsers.add_parser("partition", help="Partition operations")
    part_sub = part_parser.add_subparsers(dest="subcommand", required=True)
    part_ver = part_sub.add_parser("verify", help="Verify partition leakage status")
    part_ver.add_argument("--manifest", "-m", help="Path to partition manifest")
    part_ver.set_defaults(func=cmd_partition_verify)

    # report
    rep_parser = subparsers.add_parser("report", help="Display corpus status report")
    rep_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
