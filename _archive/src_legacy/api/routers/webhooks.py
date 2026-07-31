"""AEGIS-DocIntel — Webhook Router"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/ingest-complete")
async def ingest_complete_webhook():
    return {"received": True}
