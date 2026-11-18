"""
Adversarial Penetration Testing Pytest Fixtures & Staging Environment Setup
PROT-FINAL-03: Independent Penetration Testing & Adversarial Security Validation
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Dict, Any, Tuple
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app as gateway_app
from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.quotas import quota_manager
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.audit import audit_service
from services.evaluation_gateway.license import issue_evaluation_license, export_license_token, CANONICAL_PRODUCT
from services.evaluation_gateway.signing_key_registry import key_registry
from services.evaluation_gateway.license_repository import license_repository

from src.api.auth import get_current_tenant
from src.api.auth_guard import AuthGuardMiddleware
from src.core.security_context import TenantContext


@pytest.fixture(autouse=True)
def clean_staging_environment():
    """Ensures each adversarial penetration test operates against a fresh staging state."""
    activation_service.reset()
    audit_service.clear()
    key_registry.reset()
    license_repository.reset()
    revocation_registry.clear()
    yield
    activation_service.reset()
    audit_service.clear()
    key_registry.reset()
    license_repository.reset()
    revocation_registry.clear()


@pytest.fixture(scope="session")
def staging_rsa_keypair() -> Tuple[str, str]:
    """Generates an isolated 2048-bit RSA keypair for JWT token testing."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv_pem, pub_pem


@pytest.fixture(scope="session")
def attacker_rsa_keypair() -> Tuple[str, str]:
    """Generates an attacker's rogue RSA keypair to attempt signature forgery."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv_pem, pub_pem


@pytest.fixture(scope="session")
def staging_ed25519_keypair():
    """Generates an Ed25519 keypair for cryptographic license and device testing."""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return priv, pub


@pytest.fixture
def gateway_client():
    """TestClient targeting the evaluation gateway service."""
    return TestClient(gateway_app)


@pytest.fixture
def core_auth_app():
    """Constructs a test application with strict AuthGuardMiddleware and protected endpoints."""
    app = FastAPI(title="AEGIS-Core-Staging")
    app.add_middleware(AuthGuardMiddleware)

    # In-memory document storage segregated by tenant
    tenant_documents: Dict[str, Dict[str, Any]] = {
        "tenant-eval-a": {
            "doc-a-001": {"title": "Tenant A Secret Whitepaper", "content": "Proprietary Data A", "owner": "user-eval-a"},
            "doc-a-002": {"title": "Tenant A Financial Model", "content": "Q4 Projections", "owner": "user-eval-a"},
        },
        "tenant-eval-b": {
            "doc-b-001": {"title": "Tenant B Acquisition Memo", "content": "Target M&A Details", "owner": "user-eval-b"},
        },
    }

    # In-memory jobs segregated by tenant
    tenant_jobs: Dict[str, Dict[str, Any]] = {
        "tenant-eval-a": {
            "job-a-101": {"status": "completed", "output": "Report A Generated"},
        },
        "tenant-eval-b": {
            "job-b-202": {"status": "completed", "output": "Report B Confidential"},
        },
    }

    @app.get("/api/v1/protected")
    async def protected_endpoint(context: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": context.tenant_id,
            "principal_id": context.principal_id,
            "roles": list(context.roles),
            "status": "authenticated",
        }

    @app.get("/api/v1/documents/{doc_id}")
    async def get_document(doc_id: str, context: TenantContext = Depends(get_current_tenant)):
        docs = tenant_documents.get(context.tenant_id, {})
        if doc_id not in docs:
            # Check if it belongs to another tenant for testing disclosure resistance
            for other_tid, other_docs in tenant_documents.items():
                if other_tid != context.tenant_id and doc_id in other_docs:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=403, detail="Cross-tenant access forbidden")
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Document not found")
        return docs[doc_id]

    @app.get("/api/v1/documents/{doc_id}/export")
    async def export_document(doc_id: str, context: TenantContext = Depends(get_current_tenant)):
        docs = tenant_documents.get(context.tenant_id, {})
        if doc_id not in docs:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Access denied")
        return {"export": f"export_{doc_id}.pdf", "owner": context.tenant_id}

    @app.post("/api/v1/query")
    async def query_document(request: Request, context: TenantContext = Depends(get_current_tenant)):
        body = await request.json()
        target_doc = body.get("document_id")
        docs = tenant_documents.get(context.tenant_id, {})
        if target_doc not in docs:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Document not found in tenant catalog")
        return {"answer": "Intelligence query answer", "tenant": context.tenant_id}

    @app.post("/api/v1/documents/compare")
    async def compare_documents(request: Request, context: TenantContext = Depends(get_current_tenant)):
        body = await request.json()
        doc_ids = body.get("document_ids", [])
        docs = tenant_documents.get(context.tenant_id, {})
        for did in doc_ids:
            if did not in docs:
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail=f"Unauthorized access to document {did}")
        return {"comparison": "Valid", "documents": doc_ids}

    @app.get("/api/v1/jobs/{job_id}")
    async def get_job(job_id: str, context: TenantContext = Depends(get_current_tenant)):
        jobs = tenant_jobs.get(context.tenant_id, {})
        if job_id not in jobs:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Job not found in tenant context")
        return jobs[job_id]

    @app.post("/api/v1/admin/evaluation/quotas/policies")
    async def admin_quota_policy(request: Request, context: TenantContext = Depends(get_current_tenant)):
        if "admin" not in context.roles and "tenant_admin" not in context.roles:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin role required")
        return {"status": "policy_created"}

    @app.post("/api/v1/enterprise/batch-export")
    async def enterprise_batch_export(context: TenantContext = Depends(get_current_tenant)):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Feature 'batch_export' not licensed under evaluation edition")

    @app.post("/api/v1/enterprise/auto-redaction")
    async def enterprise_auto_redaction(context: TenantContext = Depends(get_current_tenant)):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Feature 'auto_redaction' requires enterprise license")

    return app


@pytest.fixture
def core_client(core_auth_app):
    """TestClient targeting the Core API."""
    return TestClient(core_auth_app)


@pytest.fixture
def evaluator_a_license():
    """Generates a valid evaluation license for Evaluator A."""
    lic = issue_evaluation_license(
        user_id="user-eval-a",
        duration_days=14,
        product=CANONICAL_PRODUCT,
    )
    token = export_license_token(lic)
    quota_manager.reset_usage(lic["payload"]["license_id"])
    return {
        "license_doc": lic,
        "token": token,
        "license_id": lic["payload"]["license_id"],
        "user_id": "user-eval-a",
        "tenant_id": "tenant-eval-a",
        "headers": {"X-Evaluation-License": token},
    }


@pytest.fixture
def evaluator_b_license():
    """Generates a valid evaluation license for Evaluator B."""
    lic = issue_evaluation_license(
        user_id="user-eval-b",
        duration_days=14,
        product=CANONICAL_PRODUCT,
    )
    token = export_license_token(lic)
    quota_manager.reset_usage(lic["payload"]["license_id"])
    return {
        "license_doc": lic,
        "token": token,
        "license_id": lic["payload"]["license_id"],
        "user_id": "user-eval-b",
        "tenant_id": "tenant-eval-b",
        "headers": {"X-Evaluation-License": token},
    }


def make_evaluator_jwt(
    priv_pem: str,
    tenant_id: str,
    user_id: str,
    role: str = "evaluation_user",
    iss: str = "https://auth.aegis.corp",
    aud: str = "aegis-api",
    exp_delta: int = 3600,
    nbf_delta: int = 0,
    extra_claims: Dict[str, Any] = None,
) -> str:
    now = int(time.time())
    payload = {
        "tenant_id": tenant_id,
        "sub": user_id,
        "role": role,
        "iss": iss,
        "aud": aud,
        "iat": now,
        "nbf": now + nbf_delta,
        "exp": now + exp_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, priv_pem, algorithm="RS256")


def tamper_jwt_payload(token: str, modifications: Dict[str, Any]) -> str:
    """Decodes payload segment, applies modifications without re-signing."""
    parts = token.split(".")
    assert len(parts) == 3
    header_b64, payload_b64, sig_b64 = parts
    padded = payload_b64 + "=" * (-len(payload_b64) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    claims.update(modifications)
    raw = json.dumps(claims, separators=(",", ":")).encode("utf-8")
    new_payload = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    return f"{header_b64}.{new_payload}.{sig_b64}"
