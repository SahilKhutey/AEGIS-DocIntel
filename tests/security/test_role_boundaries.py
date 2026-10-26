"""
tests/security/test_role_boundaries.py
======================================
Phase 3.1 Security Acceptance Suite — Role Boundary Enforcement:
- Viewer role: read-only queries; cannot upload, modify, delete, or access admin.
- Editor role: document upload, querying, and document lifecycle; cannot access admin.
- Admin role: unrestricted tenant access including administrative metrics and statistics.
- Unsupported role rejection: tokens with unknown roles fail validation.
"""
from __future__ import annotations

import os
import time
import uuid
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture(scope="module")
def rsa_keypair():
    """Generate an RSA 2048 keypair for cryptographic verification."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def make_token(private_pem: str, tenant_id: str, role: str, user_id: str = "test-user") -> str:
    now = int(time.time())
    payload = {
        "tenant_id": tenant_id,
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")


# ─────────────────────────────────────────────────────────────────
# Role Boundaries Tests
# ─────────────────────────────────────────────────────────────────

def test_viewer_role_cannot_upload_document(rsa_keypair):
    """Viewers cannot upload documents (HTTP 403 Forbidden)."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="viewer")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            files = {"file": ("test.txt", b"Viewer test data", "text/plain")}

            res = client.post("/v1/documents/upload", headers=headers, files=files)
            assert res.status_code == 403
            assert "Forbidden" in res.json().get("detail", "")


def test_viewer_role_cannot_delete_document(rsa_keypair):
    """Viewers cannot delete documents (HTTP 403 Forbidden)."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="viewer")
    doc_uuid = str(uuid.uuid4())

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}

            res = client.delete(f"/v1/documents/{doc_uuid}", headers=headers)
            assert res.status_code == 403
            assert "Forbidden" in res.json().get("detail", "")


def test_viewer_role_cannot_access_admin_stats(rsa_keypair):
    """Viewers cannot access administrative endpoints (HTTP 403 Forbidden)."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="viewer")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}

            res = client.get("/v1/admin/stats", headers=headers)
            assert res.status_code == 403


def test_editor_role_can_upload_but_cannot_access_admin(rsa_keypair):
    """Editors can upload documents, but cannot access administrative endpoints."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="editor")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}
            files = {"file": ("test.txt", b"Editor test data", "text/plain")}

            # Editor upload permitted
            res_upload = client.post("/v1/documents/upload", headers=headers, files=files)
            assert res_upload.status_code == 202

            # Editor admin access denied
            res_admin = client.get("/v1/admin/stats", headers=headers)
            assert res_admin.status_code == 403


def test_admin_role_can_access_admin_stats(rsa_keypair):
    """Admins can access administrative endpoints."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="admin")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}

            res = client.get("/v1/admin/stats", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert data.get("tenant_id") == "tenant-acme"


def test_unsupported_role_rejected(rsa_keypair):
    """Tokens with unauthorized/unsupported roles must fail validation (HTTP 401)."""
    private_pem, public_pem = rsa_keypair
    token = make_token(private_pem, tenant_id="tenant-acme", role="super_root_user")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
    }):
        app = create_app()
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {token}"}

            res = client.get("/v1/documents", headers=headers)
            assert res.status_code == 401
            assert "Unsupported role" in res.json().get("detail", "")
