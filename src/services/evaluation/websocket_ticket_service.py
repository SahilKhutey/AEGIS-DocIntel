"""
AEGIS-DocIntel WebSocket Ticket & Revocation Service (PROT-04 WP-04.07)
Provides single-use, short-lived ticket issuance for WebSocket handshakes,
preventing token leakage in URL parameters and enforcing real-time revocation closure.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
from src.repositories.evaluation.session_audit_repository import session_audit_repository, SessionAuditRepository
from src.services.evaluation.session_validation_service import session_validation_service, SessionValidationService


@dataclass
class WebSocketTicket:
    ticket_id: str
    session_id: str
    evaluator_id: str
    license_id: str
    device_id: str
    client_ip: str
    created_at: float
    expires_at: float
    is_consumed: bool = False


class WebSocketTicketService:
    def __init__(
        self,
        ticket_ttl_seconds: int = 60,
        val_service: Optional[SessionValidationService] = None,
        audit_repo: Optional[SessionAuditRepository] = None,
    ):
        self._lock = threading.RLock()
        self._tickets: Dict[str, WebSocketTicket] = {}
        self._ticket_ttl_seconds = ticket_ttl_seconds
        self._val_service = val_service or session_validation_service
        self._audit_repo = audit_repo or session_audit_repository
        # Track active connections: connection_id -> session_id
        self._active_connections: Dict[str, str] = {}

    def issue_ticket(
        self,
        session_id: str,
        evaluator_id: str,
        license_id: str,
        device_id: str,
        client_ip: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            ticket_id = f"aegis_ws_tkt_{secrets.token_urlsafe(32)}"
            expires_at = now + self._ticket_ttl_seconds

            ticket = WebSocketTicket(
                ticket_id=ticket_id,
                session_id=session_id,
                evaluator_id=evaluator_id,
                license_id=license_id,
                device_id=device_id,
                client_ip=client_ip,
                created_at=now,
                expires_at=expires_at,
                is_consumed=False,
            )
            self._tickets[ticket_id] = ticket

            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.WEBSOCKET_TICKET_ISSUED,
                    session_id=session_id,
                    evaluator_id=evaluator_id,
                    license_id=license_id,
                    device_id=device_id,
                    status="SUCCESS",
                    details={"ticket_id_prefix": ticket_id[:16], "ttl": self._ticket_ttl_seconds},
                )
            )

            return {
                "ticket": ticket_id,
                "expires_in": self._ticket_ttl_seconds,
                "expires_at": expires_at,
            }

    def consume_ticket(self, ticket_id: str, client_ip: str = "127.0.0.1") -> Tuple[bool, Optional[WebSocketTicket], str]:
        """
        Consumes a ticket for WebSocket connection establishment.
        Enforces single-use consumption and expiration.
        """
        with self._lock:
            now = time.time()
            ticket = self._tickets.get(ticket_id)
            if not ticket:
                return False, None, "TICKET_NOT_FOUND"

            if ticket.is_consumed:
                return False, None, "TICKET_ALREADY_CONSUMED"

            if now > ticket.expires_at:
                return False, None, "TICKET_EXPIRED"

            # Mark consumed atomically
            ticket.is_consumed = True

            self._audit_repo.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.WEBSOCKET_TICKET_CONSUMED,
                    session_id=ticket.session_id,
                    evaluator_id=ticket.evaluator_id,
                    license_id=ticket.license_id,
                    device_id=ticket.device_id,
                    status="SUCCESS",
                    details={"ticket_id_prefix": ticket_id[:16]},
                )
            )

            return True, ticket, "SUCCESS"

    def register_connection(self, connection_id: str, session_id: str) -> None:
        with self._lock:
            self._active_connections[connection_id] = session_id

    def remove_connection(self, connection_id: str) -> None:
        with self._lock:
            if connection_id in self._active_connections:
                del self._active_connections[connection_id]

    def check_connection_authorized(self, connection_id: str) -> bool:
        """Verifies that the parent session of an active WebSocket connection is still valid."""
        with self._lock:
            session_id = self._active_connections.get(connection_id)
            if not session_id:
                return False
            sess = session_repository.get_by_id(session_id)
            if not sess or not sess.is_active():
                return False
            return True

    def clear(self) -> None:
        with self._lock:
            self._tickets.clear()
            self._active_connections.clear()


websocket_ticket_service = WebSocketTicketService()
