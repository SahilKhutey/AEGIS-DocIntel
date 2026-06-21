"""
AEGIS-DocIntel — Admin & Webhook Stubs
========================================
Placeholder routers for admin and webhook endpoints.
"""
from fastapi import APIRouter

admin = APIRouter()
webhooks = APIRouter()

router = admin  # expose as `admin.router`

@admin.get("/stats")
async def get_stats():
    return {"message": "Admin stats endpoint — implement with container.admin_service"}

@admin.get("/token-usage")
async def get_token_usage():
    return {"message": "Token usage endpoint"}
