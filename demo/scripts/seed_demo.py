"""
AEGIS-DocIntel — Demo Seed Script
===================================
Seeds the synthetic technical documentation corpus for 'demo-tenant'.
Can be executed as a CLI script, a startup hook, or via the Demo API router.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import structlog

log = structlog.get_logger("aegis.demo.seed")

DEMO_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = DEMO_DIR / "seed" / "manifest.json"
DOCS_DIR = DEMO_DIR / "seed" / "documents"


def load_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_items(docs_result: Any) -> List[Any]:
    if hasattr(docs_result, "items"):
        return getattr(docs_result, "items", [])
    if isinstance(docs_result, dict):
        return docs_result.get("items", [])
    if isinstance(docs_result, list):
        return docs_result
    return []


def _get_attr(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


async def seed_in_process(container: Any, tenant_id: str = "demo-tenant") -> List[Dict[str, Any]]:
    """Seed synthetic documents directly into the active ServiceContainer."""
    manifest = load_manifest()
    results = []

    doc_service = getattr(container, "document_service", None)
    if not doc_service:
        raise RuntimeError("ServiceContainer does not have an active document_service")

    # Check existing documents for this tenant to avoid redundant re-indexing
    existing_res = await doc_service.list_documents(tenant_id=tenant_id)
    existing_items = _extract_items(existing_res)
    existing_filenames = {
        _get_attr(d, "filename"): _get_attr(d, "doc_id") for d in existing_items
    }

    for item in manifest.get("documents", []):
        filename = item["filename"]
        file_path = DOCS_DIR / filename
        if not file_path.exists():
            log.warning("Seed document file missing", filename=filename, path=str(file_path))
            continue

        if filename in existing_filenames:
            log.info("Seed document already present", filename=filename, doc_id=existing_filenames[filename])
            results.append({"filename": filename, "doc_id": existing_filenames[filename], "status": "existing"})
            continue

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        log.info("Ingesting seed document", filename=filename, size=len(file_bytes), tenant_id=tenant_id)
        content_type = item.get("content_type", "text/plain")
        ingested = await doc_service.ingest(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            tenant_id=tenant_id,
        )
        doc_id = ingested.get("doc_id") if isinstance(ingested, dict) else str(ingested)
        results.append({"filename": filename, "doc_id": doc_id, "status": "seeded"})
        log.info("Successfully seeded document", filename=filename, doc_id=doc_id)

    return results


async def seed_via_api(
    base_url: str = "http://127.0.0.1:8000",
    token: str = "aegis-demo-token-sandbox",
    tenant_id: str = "demo-tenant",
) -> List[Dict[str, Any]]:
    """Seed synthetic documents over HTTP API into the demo workspace."""
    manifest = load_manifest()
    results = []
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
    }

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=60.0) as client:
        # Check existing
        list_res = await client.get("/api/v1/documents", headers=headers)
        existing_filenames = set()
        if list_res.status_code == 200:
            data = list_res.json()
            for doc in data.get("items", []):
                existing_filenames.add(doc.get("filename"))

        for item in manifest.get("documents", []):
            filename = item["filename"]
            file_path = DOCS_DIR / filename
            if not file_path.exists():
                log.warning("Seed document missing", filename=filename)
                continue

            if filename in existing_filenames:
                log.info("Document already present via API", filename=filename)
                results.append({"filename": filename, "status": "existing"})
                continue

            with open(file_path, "rb") as f:
                content = f.read()

            files = {"file": (filename, content, item.get("content_type", "text/plain"))}
            upload_res = await client.post("/api/v1/documents", headers=headers, files=files)
            if upload_res.status_code in (200, 201, 202):
                doc_id = upload_res.json().get("doc_id")
                results.append({"filename": filename, "doc_id": doc_id, "status": "seeded"})
                log.info("Uploaded seed document via API", filename=filename, doc_id=doc_id)
            else:
                log.error("Failed to seed via API", filename=filename, status=upload_res.status_code, body=upload_res.text)

    return results


def main():
    parser = argparse.ArgumentParser(description="AEGIS-DocIntel Demo Seeder")
    parser.add_argument("--api-url", default=None, help="Seed via HTTP API endpoint (e.g. http://127.0.0.1:8000)")
    parser.add_argument("--token", default=os.environ.get("AEGIS_DEMO_TOKEN", "aegis-demo-token-sandbox"))
    parser.add_argument("--tenant", default="demo-tenant")
    args = parser.parse_args()

    if args.api_url:
        print(f"Seeding demo corpus via API at {args.api_url}...")
        res = asyncio.run(seed_via_api(base_url=args.api_url, token=args.token, tenant_id=args.tenant))
        print(f"Seeding completed. {len(res)} documents processed: {res}")
    else:
        # Standalone container startup
        print("Initializing standalone container for in-process seeding...")
        from src.config import settings
        from src.services.container import ServiceContainer
        container = ServiceContainer(settings)
        async def run_standalone():
            await container.startup()
            try:
                res = await seed_in_process(container, tenant_id=args.tenant)
                print(f"In-process seeding complete. Seeded: {res}")
            finally:
                await container.shutdown()
        asyncio.run(run_standalone())


if __name__ == "__main__":
    main()
