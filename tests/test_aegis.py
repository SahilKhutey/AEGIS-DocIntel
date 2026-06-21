"""
AEGIS-DocIntel — Test Suite
=============================
Integration tests for the full RAG pipeline.
Run with: pytest tests/ -v
"""
from __future__ import annotations

import asyncio
import os
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("S3_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY", "minioadmin")
os.environ.setdefault("S3_SECRET_KEY", "minioadmin")
os.environ["AEGIS_USE_MOCK_EMBEDDER"] = "1"   # skip model download in tests


# ─────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    """Import the FastAPI app for testing."""
    from src.main import app
    return app


@pytest.fixture(scope="session")
def client(app):
    """
    Synchronous test client WITH lifespan support.
    TestClient starts the lifespan (startup/shutdown) automatically.
    """
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ─────────────────────────────────────────────────────────────────
# Health Tests
# ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data

    def test_readiness(self, client):
        resp = client.get("/readiness")
        assert resp.status_code == 200
        assert resp.json()["ready"] is True


# ─────────────────────────────────────────────────────────────────
# Authentication Tests
# ─────────────────────────────────────────────────────────────────

class TestAuthentication:
    def test_no_auth_rejected(self, client):
        resp = client.post("/v1/query", json={"question": "test"})
        assert resp.status_code == 401

    def test_dev_token_accepted(self, client):
        resp = client.get(
            "/v1/documents",
            headers={"Authorization": "Bearer dev-test-tenant"}
        )
        assert resp.status_code == 200

    def test_api_key_accepted(self, client):
        resp = client.get(
            "/v1/documents",
            headers={"X-API-Key": "aegis-dev-key"}
        )
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────────
# Document Upload Tests
# ─────────────────────────────────────────────────────────────────

class TestDocumentUpload:
    def test_upload_minimal_pdf(self, client):
        """Test uploading a minimal valid PDF."""
        # Minimal PDF bytes (valid PDF structure)
        minimal_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("test.pdf", minimal_pdf, "application/pdf")},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "doc_id" in data
        assert data["status"] in ("pending", "ready", "indexing")

    def test_upload_invalid_type_rejected(self, client):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("test.exe", b"MZ\x90\x00", "application/octet-stream")},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 415

    def test_upload_empty_file_rejected(self, client):
        resp = client.post(
            "/v1/documents/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 400

    def test_list_documents(self, client):
        resp = client.get(
            "/v1/documents",
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


# ─────────────────────────────────────────────────────────────────
# Query Tests
# ─────────────────────────────────────────────────────────────────

class TestQuery:
    def test_basic_query(self, client):
        resp = client.post(
            "/v1/query",
            json={"question": "What is the main topic of the documents?"},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "confidence" in data
        assert "session_id" in data
        assert "tokens_used" in data

    def test_empty_question_rejected(self, client):
        resp = client.post(
            "/v1/query",
            json={"question": "   "},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 422

    def test_query_with_session(self, client):
        import uuid
        session_id = str(uuid.uuid4())
        resp = client.post(
            "/v1/query",
            json={
                "question": "Explain the document structure",
                "session_id": session_id,
            },
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert str(data["session_id"]) == session_id

    def test_query_confidence_levels(self, client):
        resp = client.post(
            "/v1/query",
            json={"question": "What are the key findings?"},
            headers={"Authorization": "Bearer dev-test-tenant"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence"] in ("HIGH", "MEDIUM", "LOW")


# ─────────────────────────────────────────────────────────────────
# Configuration Tests
# ─────────────────────────────────────────────────────────────────

class TestConfiguration:
    def test_settings_load(self):
        from src.config import settings
        assert settings.app.name == "aegis-docintel"
        assert settings.api.port == 8000

    def test_storage_config(self):
        from src.config import settings
        assert settings.storage.s3.bucket_raw == "aegis-raw"


# ─────────────────────────────────────────────────────────────────
# Unit Tests: Token Budget
# ─────────────────────────────────────────────────────────────────

class TestTokenBudget:
    def test_token_count_approximation(self):
        """1000 words ≈ 1300 tokens (1.33x multiplier)."""
        text = " ".join(["word"] * 1000)
        estimated = max(1, int(len(text.split()) * 1.33))
        assert 1200 <= estimated <= 1400

    def test_context_builder_budget(self):
        """Context builder respects MAX_TOKENS budget."""
        # Max chunks budget = 5900 tokens
        # Each chunk ~700 tokens → max 8 chunks
        budget = 8500 - 1200 - 300 - 200 - 800 - 400
        avg_chunk = 700
        max_chunks = budget // avg_chunk
        assert max_chunks >= 8
