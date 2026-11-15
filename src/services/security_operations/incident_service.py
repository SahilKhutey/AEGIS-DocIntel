"""
AEGIS-DocIntel Incident Response Coordination Service (PROT-04 WP-04.08)
Coordinates incident lifecycle: detection, containment, evidence preservation,
recovery, and close condition enforcement.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from src.repositories.security_operations.incident_repository import (
    IncidentRecord,
    IncidentRepository,
    IncidentStatus,
    incident_repository,
)

logger = logging.getLogger("aegis.security.incidents")


class IncidentService:
    def __init__(self, incident_repo: Optional[IncidentRepository] = None):
        self._repo = incident_repo or incident_repository

    def declare_incident(
        self,
        threat_id: str,
        severity: str,
        title: str,
        description: str,
    ) -> IncidentRecord:
        """Declares an incident and records initial state."""
        inc = self._repo.create_incident(
            threat_id=threat_id,
            severity=severity,
            title=title,
            description=description,
        )
        logger.warning("Security incident declared: [%s] %s (Severity: %s)", inc.incident_id, title, severity)
        return inc

    def contain_incident(self, incident_id: str, containment_action: str) -> IncidentRecord:
        """Records containment action and transitions state to CONTAINED."""
        inc = self._repo.record_containment(incident_id, containment_action)
        logger.info("Incident [%s] contained: %s", incident_id, containment_action)
        return inc

    def preserve_evidence(self, incident_id: str, evidence_id: str) -> IncidentRecord:
        """Links preserved forensic artifact or audit export to the incident."""
        inc = self._repo.attach_evidence(incident_id, evidence_id)
        logger.info("Forensic evidence [%s] attached to incident [%s]", evidence_id, incident_id)
        return inc

    def close_incident(self, incident_id: str, resolution_notes: str) -> IncidentRecord:
        """
        Closes incident.
        Enforces IR-008: Rejects closure if no evidence IDs were preserved during investigation.
        """
        return self._repo.close_incident(incident_id, resolution_notes)

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        return self._repo.get_incident(incident_id)

    def list_incidents(self) -> List[IncidentRecord]:
        return self._repo.list_incidents()


incident_service = IncidentService()
