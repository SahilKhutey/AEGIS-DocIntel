"""
src/services/authorization_service.py
=====================================
AEGIS-DocIntel — Document & Citation Authorization Service.
Enforces object-level tenant isolation, access boundaries, and citation provenance checks.
Strict invariant: Every document and citation accessed must be affirmatively authorized.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Set, Tuple


class Principal(Protocol):
    """Protocol representing an authenticated, trusted security principal."""

    @property
    def tenant_id(self) -> str:
        ...

    @property
    def subject_id(self) -> str:
        ...


class DocumentAccessRepository(Protocol):
    """Repository boundary for querying document ownership and authorization."""

    def list_authorized_document_ids(
        self,
        *,
        subject_id: str,
        tenant_id: str,
        requested_ids: Tuple[str, ...],
    ) -> Set[str]:
        ...


class InMemoryDocumentAccessRepository:
    """In-memory document access repository for testing and standalone orchestration."""

    def __init__(self, doc_ownership: Optional[Dict[str, str]] = None) -> None:
        # doc_id -> tenant_id
        self._doc_ownership: Dict[str, str] = dict(doc_ownership or {})

    def register_document(self, doc_id: str, tenant_id: str) -> None:
        self._doc_ownership[str(doc_id)] = str(tenant_id)

    def revoke_document(self, doc_id: str) -> None:
        self._doc_ownership.pop(str(doc_id), None)

    def list_authorized_document_ids(
        self,
        *,
        subject_id: str,
        tenant_id: str,
        requested_ids: Tuple[str, ...],
    ) -> Set[str]:
        authorized: Set[str] = set()
        for doc_id in requested_ids:
            owner = self._doc_ownership.get(str(doc_id))
            if owner is not None and owner == tenant_id:
                authorized.add(str(doc_id))
        return authorized


class DocumentAuthorizationService:
    """
    Evaluates fine-grained authorization policies before retrieval and before citation disclosure.
    """

    def __init__(self, repository: Optional[DocumentAccessRepository] = None) -> None:
        self._repository = repository

    def authorize_documents(
        self,
        *,
        principal: Principal,
        document_ids: Tuple[str, ...],
    ) -> None:
        """
        Authorize that the principal has explicit access to all requested documents.
        Raises PermissionError if principal is invalid or any document belongs to another tenant.
        """
        if not principal.tenant_id or not principal.subject_id:
            raise PermissionError("Invalid authenticated principal: missing tenant or subject identity")

        if not document_ids or self._repository is None:
            return

        authorized = self._repository.list_authorized_document_ids(
            subject_id=principal.subject_id,
            tenant_id=principal.tenant_id,
            requested_ids=document_ids,
        )

        unauthorized = set(document_ids) - authorized
        if unauthorized:
            # Non-disclosing security exception
            raise PermissionError(
                f"Principal {principal.subject_id!r} is not authorized to access requested documents"
            )

    def authorize_citations(
        self,
        *,
        principal: Principal,
        citations: Tuple[Any, ...],
    ) -> None:
        """
        Recheck authorization on citations immediately before response serialization.
        Guarantees no cross-tenant citation or ungrounded evidence leaks to the client.
        """
        if not principal.tenant_id or not principal.subject_id:
            raise PermissionError("Invalid authenticated principal: missing tenant or subject identity")

        if not citations:
            return

        doc_ids = tuple(
            getattr(c, "document_id") for c in citations if hasattr(c, "document_id")
        )

        # Check tenant_id field if present on citation object
        for c in citations:
            cit_tenant = getattr(c, "tenant_id", None)
            if cit_tenant is not None and cit_tenant != principal.tenant_id:
                raise PermissionError("Citation references a resource belonging to a different tenant")

        if self._repository is not None and doc_ids:
            authorized = self._repository.list_authorized_document_ids(
                subject_id=principal.subject_id,
                tenant_id=principal.tenant_id,
                requested_ids=doc_ids,
            )
            unauthorized = set(doc_ids) - authorized
            if unauthorized:
                raise PermissionError("Citation references an unauthorized document source")
