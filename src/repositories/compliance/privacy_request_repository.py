"""
AEGIS-DocIntel Privacy Request Repository
PROT-FINAL-07: Workstream 07.07

Manages data subject privacy requests with strict tenant isolation (COMP-008, COMP-010):
- Requests are partitioned by tenant_id
- Cross-tenant request lookup is explicitly denied
- Tracks execution actions across documents, vector embeddings, and caches
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aegis.compliance.privacy_request_repository")


class PrivacyRequestRepository:
    def __init__(self):
        # (tenant_id, request_id) -> request_dict
        self._requests: Dict[tuple[str, str], Dict[str, Any]] = {}
        # request_id -> list of action dicts
        self._actions: Dict[str, List[Dict[str, Any]]] = {}

    def create_request(
        self,
        tenant_id: str,
        requester_id: str,
        request_type: str,
        assigned_owner: str = "privacy_owner",
    ) -> Dict[str, Any]:
        req_id = f"dsr-{uuid.uuid4().hex[:8]}"
        ref_num = f"DSR-2026-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "id": req_id,
            "request_reference": ref_num,
            "requester_id": requester_id,
            "tenant_id": tenant_id,
            "request_type": request_type,
            "status": "RECEIVED",
            "received_at": now,
            "verified_at": None,
            "completed_at": None,
            "assigned_owner": assigned_owner,
            "decision_reason": None,
            "verification_evidence_id": None,
        }
        self._requests[(tenant_id, req_id)] = record
        self._actions[req_id] = []
        return record

    def get_request(self, tenant_id: str, request_id: str) -> Optional[Dict[str, Any]]:
        """
        COMP-008: Parameterized tenant isolation.
        Returns None if request does not belong to the authenticated tenant.
        """
        return self._requests.get((tenant_id, request_id))

    def update_status(
        self,
        tenant_id: str,
        request_id: str,
        status: str,
        reason: Optional[str] = None,
        evidence_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        record = self.get_request(tenant_id, request_id)
        if not record:
            return None
        record["status"] = status
        now = datetime.now(timezone.utc).isoformat()
        if status == "VERIFIED" and not record["verified_at"]:
            record["verified_at"] = now
        elif status in {"EXECUTED", "VERIFIED_CLOSED", "CLOSED"}:
            record["completed_at"] = now
        if reason:
            record["decision_reason"] = reason
        if evidence_id:
            record["verification_evidence_id"] = evidence_id
        return record

    def record_action(
        self,
        request_id: str,
        system_name: str,
        action_type: str,
        result: str,
    ) -> Dict[str, Any]:
        action_id = f"act-{uuid.uuid4().hex[:8]}"
        action = {
            "id": action_id,
            "request_id": request_id,
            "system_name": system_name,
            "action_type": action_type,
            "result": result,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._actions.setdefault(request_id, []).append(action)
        return action

    def list_actions(self, request_id: str) -> List[Dict[str, Any]]:
        return self._actions.get(request_id, [])

    def list_requests(self, tenant_id: str) -> List[Dict[str, Any]]:
        return [r for (t_id, _), r in self._requests.items() if t_id == tenant_id]

    def clear(self) -> None:
        self._requests.clear()
        self._actions.clear()


privacy_request_repository = PrivacyRequestRepository()
