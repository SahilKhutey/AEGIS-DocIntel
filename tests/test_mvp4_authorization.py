"""
tests/test_mvp4_authorization.py
================================
Unit tests for DocumentAuthorizationService and Principal protocol adherence.
"""

from __future__ import annotations

import pytest
from src.core.security_context import TenantContext
from src.services.authorization_service import (
    DocumentAuthorizationService,
    InMemoryDocumentAccessRepository,
)


class MockPrincipal:
    def __init__(self, tenant_id: str, subject_id: str) -> None:
        self._tenant_id = tenant_id
        self._subject_id = subject_id

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def subject_id(self) -> str:
        return self._subject_id


class MockCitation:
    def __init__(self, document_id: str, tenant_id: str | None = None) -> None:
        self.document_id = document_id
        self.tenant_id = tenant_id


def test_tenant_context_satisfies_principal_protocol():
    ctx = TenantContext(tenant_id="tenant-123", principal_id="user-456", roles={"viewer"})
    assert ctx.tenant_id == "tenant-123"
    assert ctx.subject_id == "user-456"


def test_missing_principal_identity_fails():
    auth_service = DocumentAuthorizationService()
    invalid_principal = MockPrincipal("", "")
    with pytest.raises(PermissionError, match="Invalid authenticated principal"):
        auth_service.authorize_documents(principal=invalid_principal, document_ids=("doc-1",))

    with pytest.raises(PermissionError, match="Invalid authenticated principal"):
        auth_service.authorize_citations(principal=invalid_principal, citations=(MockCitation("doc-1"),))


def test_authorized_documents_pass():
    repo = InMemoryDocumentAccessRepository({"doc-1": "tenant-alpha", "doc-2": "tenant-alpha"})
    auth_service = DocumentAuthorizationService(repo)
    principal = MockPrincipal("tenant-alpha", "user-1")

    # Should not raise
    auth_service.authorize_documents(principal=principal, document_ids=("doc-1", "doc-2"))


def test_cross_tenant_document_access_is_denied():
    repo = InMemoryDocumentAccessRepository({"doc-1": "tenant-alpha", "doc-2": "tenant-beta"})
    auth_service = DocumentAuthorizationService(repo)
    principal = MockPrincipal("tenant-alpha", "user-1")

    with pytest.raises(PermissionError, match="not authorized"):
        auth_service.authorize_documents(principal=principal, document_ids=("doc-1", "doc-2"))


def test_citation_tenant_mismatch_is_rejected():
    repo = InMemoryDocumentAccessRepository({"doc-1": "tenant-alpha"})
    auth_service = DocumentAuthorizationService(repo)
    principal = MockPrincipal("tenant-alpha", "user-1")

    # Citation carrying cross-tenant identifier
    bad_citation = MockCitation(document_id="doc-1", tenant_id="tenant-beta")
    with pytest.raises(PermissionError, match="different tenant"):
        auth_service.authorize_citations(principal=principal, citations=(bad_citation,))


def test_citation_unauthorized_document_is_rejected():
    repo = InMemoryDocumentAccessRepository({"doc-1": "tenant-alpha"})
    auth_service = DocumentAuthorizationService(repo)
    principal = MockPrincipal("tenant-alpha", "user-1")

    # Citation references a doc not in tenant's authorized repository
    rogue_citation = MockCitation(document_id="doc-secret", tenant_id="tenant-alpha")
    with pytest.raises(PermissionError, match="unauthorized document source"):
        auth_service.authorize_citations(principal=principal, citations=(rogue_citation,))
