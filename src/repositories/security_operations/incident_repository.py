"""
AEGIS-DocIntel Incident Repository (PROT-04 WP-04.08)
Tracks security incidents, containment actions, evidence lineages, and close conditions.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4


class IncidentStatus(str, Enum):
    OPEN = "open"
    CONTAINED = "contained"
    INVESTIGATING = "investigating"
    RECOVERED = "recovered"
    CLOSED = "closed"


@dataclass
class IncidentRecord:
    incident_id: str
    threat_id: str
    severity: str
    title: str
    description: str
    status: IncidentStatus
    created_at: datetime
    contained_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    containment_actions: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
    resolution_notes: Optional[str] = None


class IncidentRepository:
    def __init__(self):
        self._lock = threading.RLock()
        self._incidents: Dict[str, IncidentRecord] = {}

    def create_incident(
        self,
        threat_id: str,
        severity: str,
        title: str,
        description: str,
    ) -> IncidentRecord:
        with self._lock:
            inc_id = f"inc-{uuid4().hex[:8]}"
            record = IncidentRecord(
                incident_id=inc_id,
                threat_id=threat_id,
                severity=severity,
                title=title,
                description=description,
                status=IncidentStatus.OPEN,
                created_at=datetime.now(timezone.utc),
            )
            self._incidents[inc_id] = record
            return record

    def record_containment(self, incident_id: str, action: str) -> IncidentRecord:
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                raise KeyError(f"Incident '{incident_id}' not found.")
            inc.containment_actions.append(action)
            inc.status = IncidentStatus.CONTAINED
            inc.contained_at = datetime.now(timezone.utc)
            return inc

    def attach_evidence(self, incident_id: str, evidence_id: str) -> IncidentRecord:
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                raise KeyError(f"Incident '{incident_id}' not found.")
            inc.evidence_ids.append(evidence_id)
            return inc

    def close_incident(self, incident_id: str, resolution_notes: str) -> IncidentRecord:
        """
        Closes a security incident.
        Enforces IR-008: Incidents cannot be closed without verified evidence IDs attached.
        """
        with self._lock:
            inc = self._incidents.get(incident_id)
            if not inc:
                raise KeyError(f"Incident '{incident_id}' not found.")

            if not inc.evidence_ids:
                raise ValueError(
                    f"Incident '{incident_id}' cannot be closed without preserved evidence. "
                    "Attach evidence IDs before closure (IR-008)."
                )

            inc.status = IncidentStatus.CLOSED
            inc.closed_at = datetime.now(timezone.utc)
            inc.resolution_notes = resolution_notes
            return inc

    def get_incident(self, incident_id: str) -> Optional[IncidentRecord]:
        with self._lock:
            return self._incidents.get(incident_id)

    def list_incidents(self) -> List[IncidentRecord]:
        with self._lock:
            return list(self._incidents.values())

    def clear(self) -> None:
        with self._lock:
            self._incidents.clear()


incident_repository = IncidentRepository()
