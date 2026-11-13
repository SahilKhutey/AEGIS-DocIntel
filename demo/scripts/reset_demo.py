"""
AEGIS-DocIntel — Demo Reset Script
====================================
Atomically wipes demo tenant documents and re-seeds from pristine manifest.
Ensures every visitor evaluates AEGIS against a known, reproducible benchmark state.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
import structlog

from demo.scripts.seed_demo import seed_in_process, seed_via_api

log = structlog.get_logger("aegis.demo.reset")


async def execute_demo_reset(container: Any, tenant_id: str = "demo-tenant") -> int:
    """In-process execution of demo reset: deletes existing demo docs and re-seeds."""
    doc_service = getattr(container, "document_service", None)
    if not doc_service:
        raise RuntimeError("ServiceContainer does not have an active document_service")

    log.info("Starting demo workspace reset", tenant_id=tenant_id)

    # 1. List and delete existing documents for demo-tenant
    existing_res = await doc_service.list_documents(tenant_id=tenant_id)
    items = getattr(existing_res, "items", existing_res if isinstance(existing_res, list) else [])
    deleted_count = 0
    for doc in items:
        doc_id = doc.get("doc_id") if isinstance(doc, dict) else getattr(doc, "doc_id", None)
        if doc_id:
            try:
                await doc_service.delete(doc_id=doc_id, tenant_id=tenant_id)
                deleted_count += 1
            except Exception as e:
                log.warning("Could not delete demo document during reset", doc_id=doc_id, error=str(e))

    log.info("Purged existing demo documents", count=deleted_count, tenant_id=tenant_id)

    # 2. Re-seed from manifest
    seeded = await seed_in_process(container, tenant_id=tenant_id)
    log.info("Re-seeded pristine demo documents", count=len(seeded), tenant_id=tenant_id)
    return len(seeded)


async def reset_via_api(
    base_url: str = "http://127.0.0.1:8000",
    token: str = "aegis-demo-token-sandbox",
    tenant_id: str = "demo-tenant",
) -> Dict[str, Any]:
    """Execute reset over HTTP API via /api/v1/demo/reset."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
    }

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=60.0) as client:
        res = await client.post("/api/v1/demo/reset", headers=headers)
        if res.status_code == 200:
            return res.json()

        # Fallback manual reset if /demo/reset endpoint not active
        log.warning("Reset endpoint returned non-200, falling back to manual API delete + re-seed", status=res.status_code)
        list_res = await client.get("/api/v1/documents", headers=headers)
        if list_res.status_code == 200:
            items = list_res.json().get("items", [])
            for doc in items:
                await client.delete(f"/api/v1/documents/{doc.get('doc_id')}", headers=headers)

        seeded = await seed_via_api(base_url=base_url, token=token, tenant_id=tenant_id)
        return {"status": "success", "tenant_id": tenant_id, "documents_restored": len(seeded)}


def main():
    parser = argparse.ArgumentParser(description="AEGIS-DocIntel Demo Workspace Reset")
    parser.add_argument("--api-url", default=None, help="Reset via HTTP API endpoint")
    parser.add_argument("--token", default=os.environ.get("AEGIS_DEMO_TOKEN", "aegis-demo-token-sandbox"))
    parser.add_argument("--tenant", default="demo-tenant")
    args = parser.parse_args()

    if args.api_url:
        print(f"Resetting demo workspace via API at {args.api_url}...")
        res = asyncio.run(reset_via_api(base_url=args.api_url, token=args.token, tenant_id=args.tenant))
        print(f"Demo reset complete: {res}")
    else:
        print("Running in-process demo reset...")
        from src.config import settings
        from src.services.container import ServiceContainer
        container = ServiceContainer(settings)
        async def run_standalone():
            await container.startup()
            try:
                count = await execute_demo_reset(container, tenant_id=args.tenant)
                print(f"In-process reset complete. {count} documents restored.")
            finally:
                await container.shutdown()
        asyncio.run(run_standalone())


if __name__ == "__main__":
    main()
