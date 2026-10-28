"""
src/repositories/review_repository.py
=====================================
SQLite-backed, tenant-isolated transactional repository for review items,
decisions, revisions, append-only audit events, and feedback.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.engines.governance.contracts import (
    AuditEvent,
    CandidateType,
    ReviewAction,
    ReviewDecision,
    ReviewItem,
    ReviewRevision,
    ReviewStatus,
)
from src.engines.governance.feedback import FeedbackCategory, ReviewFeedback


class ReviewNotFoundError(KeyError):
    """Raised when a review item cannot be found for the specified tenant."""
    pass


class StaleReviewVersionError(ValueError):
    """Raised when an action is submitted against a stale version of a review item."""
    pass


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused with a conflicting payload."""
    pass


class ReviewRepository:
    """
    Data access layer managing review items, decisions, revisions, audit trails, and feedback.
    Enforces optimistic concurrency, append-only audit trails, and transactional transitions.
    """

    def __init__(self, db_path: str = "data/review_governance.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if not hasattr(self, "_mem_conn") or self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_items (
                        review_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        candidate_id TEXT NOT NULL,
                        candidate_type TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        version INTEGER NOT NULL DEFAULT 1,
                        assigned_to TEXT,
                        candidate_data_json TEXT NOT NULL,
                        current_revision_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_review_tenant_status
                    ON review_items(tenant_id, status, created_at)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_review_tenant_assigned
                    ON review_items(tenant_id, assigned_to, status)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_review_candidate
                    ON review_items(tenant_id, candidate_id)
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_decisions (
                        decision_id TEXT PRIMARY KEY,
                        review_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        from_status TEXT NOT NULL,
                        to_status TEXT NOT NULL,
                        version_reviewed INTEGER NOT NULL,
                        rationale TEXT NOT NULL,
                        evidence_quote TEXT,
                        idempotency_key TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (review_id) REFERENCES review_items(review_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_decisions_review
                    ON review_decisions(review_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_decisions_idempotency
                    ON review_decisions(tenant_id, review_id, idempotency_key)
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_revisions (
                        revision_id TEXT PRIMARY KEY,
                        review_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        corrected_value_json TEXT NOT NULL,
                        corrected_type TEXT NOT NULL,
                        unit TEXT,
                        evidence_quote TEXT,
                        rationale TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (review_id) REFERENCES review_items(review_id) ON DELETE CASCADE
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_audit_events (
                        event_id TEXT PRIMARY KEY,
                        review_id TEXT NOT NULL,
                        sequence INTEGER NOT NULL,
                        tenant_id TEXT NOT NULL,
                        actor_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        previous_status TEXT NOT NULL,
                        new_status TEXT NOT NULL,
                        previous_version INTEGER NOT NULL,
                        new_version INTEGER NOT NULL,
                        revision_id TEXT,
                        rationale TEXT NOT NULL,
                        request_id TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (review_id) REFERENCES review_items(review_id) ON DELETE CASCADE,
                        UNIQUE (review_id, sequence)
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_review_seq
                    ON review_audit_events(review_id, sequence ASC)
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS review_feedback (
                        feedback_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        review_id TEXT NOT NULL,
                        candidate_id TEXT NOT NULL,
                        category TEXT NOT NULL,
                        reviewer_id TEXT NOT NULL,
                        notes TEXT,
                        corrected_value_reference TEXT,
                        schema_version INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_feedback_tenant
                    ON review_feedback(tenant_id, review_id)
                """)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def create_review_item(
        self,
        tenant_id: str,
        candidate_id: str,
        candidate_type: CandidateType,
        document_id: str,
        candidate_data: Dict[str, Any],
        assigned_to: Optional[str] = None,
    ) -> ReviewItem:
        """
        Create a new review queue item for an extracted fact or conflict.
        If an item already exists for (tenant_id, candidate_id), returns the existing item.
        """
        conn = self._get_connection()
        try:
            with conn:
                existing = conn.execute(
                    """
                    SELECT * FROM review_items
                    WHERE tenant_id = ? AND candidate_id = ?
                    """,
                    (tenant_id, candidate_id),
                ).fetchone()

                if existing:
                    return self._row_to_review_item(existing)

                review_id = f"rev-{uuid.uuid4().hex}"
                now = datetime.now(timezone.utc).isoformat()
                cand_json = json.dumps(candidate_data)

                conn.execute(
                    """
                    INSERT INTO review_items (
                        review_id, tenant_id, candidate_id, candidate_type,
                        document_id, status, version, assigned_to,
                        candidate_data_json, current_revision_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        review_id,
                        tenant_id,
                        candidate_id,
                        candidate_type,
                        document_id,
                        str(ReviewStatus.PENDING),
                        1,
                        assigned_to,
                        cand_json,
                        None,
                        now,
                        now,
                    ),
                )

                # Initialize initial audit event for creation
                init_event_id = f"evt-{uuid.uuid4().hex}"
                conn.execute(
                    """
                    INSERT INTO review_audit_events (
                        event_id, review_id, sequence, tenant_id, actor_id,
                        action, previous_status, new_status, previous_version,
                        new_version, revision_id, rationale, request_id, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        init_event_id,
                        review_id,
                        1,
                        tenant_id,
                        "system",
                        "create",
                        str(ReviewStatus.PENDING),
                        str(ReviewStatus.PENDING),
                        1,
                        1,
                        None,
                        "Review item created from candidate ingestion",
                        None,
                        now,
                    ),
                )

                row = conn.execute(
                    "SELECT * FROM review_items WHERE review_id = ?",
                    (review_id,),
                ).fetchone()
                return self._row_to_review_item(row)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_review(self, tenant_id: str, review_id: str) -> Optional[ReviewItem]:
        """Fetch a single review item within tenant boundary."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM review_items WHERE tenant_id = ? AND review_id = ?",
                (tenant_id, review_id),
            ).fetchone()
            return self._row_to_review_item(row) if row else None
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def list_reviews(
        self,
        tenant_id: str,
        status: Optional[ReviewStatus] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Tuple[List[ReviewItem], Optional[str]]:
        """
        List review queue items scoped to tenant, with cursor-based pagination.
        Cursor format: ISO timestamp of created_at.
        """
        conn = self._get_connection()
        try:
            query = "SELECT * FROM review_items WHERE tenant_id = ?"
            params: List[Any] = [tenant_id]

            if status:
                query += " AND status = ?"
                params.append(str(status))
            if assigned_to:
                query += " AND assigned_to = ?"
                params.append(assigned_to)
            if cursor:
                query += " AND created_at < ?"
                params.append(cursor)

            query += " ORDER BY created_at DESC, review_id DESC LIMIT ?"
            params.append(limit + 1)

            rows = conn.execute(query, params).fetchall()
            items = [self._row_to_review_item(r) for r in rows[:limit]]

            next_cursor = None
            if len(rows) > limit:
                next_cursor = items[-1].created_at

            return items, next_cursor
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_idempotent_decision(
        self,
        tenant_id: str,
        review_id: str,
        idempotency_key: str,
    ) -> Optional[Tuple[ReviewItem, ReviewDecision, AuditEvent]]:
        """Check for a previously executed decision with the given idempotency key."""
        conn = self._get_connection()
        try:
            cached = conn.execute(
                """
                SELECT * FROM review_decisions
                WHERE tenant_id = ? AND review_id = ? AND idempotency_key = ?
                """,
                (tenant_id, review_id, idempotency_key),
            ).fetchone()
            if not cached:
                return None
            cached_dec = self._row_to_decision(cached)
            item = self.get_review(tenant_id, review_id)
            if not item:
                return None
            last_event = conn.execute(
                """
                SELECT * FROM review_audit_events
                WHERE review_id = ? ORDER BY sequence DESC LIMIT 1
                """,
                (review_id,),
            ).fetchone()
            audit_ev = (
                self._row_to_audit_event(last_event)
                if last_event
                else AuditEvent(
                    event_id="cached",
                    review_id=review_id,
                    sequence=1,
                    tenant_id=tenant_id,
                    actor_id=cached_dec.actor_id,
                    action=cached_dec.action,
                    previous_status=cached_dec.from_status,
                    new_status=cached_dec.to_status,
                    previous_version=cached_dec.version_reviewed,
                    new_version=cached_dec.version_reviewed,
                    rationale=cached_dec.rationale,
                    timestamp=cached_dec.created_at,
                )
            )
            return item, cached_dec, audit_ev
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def save_transition(
        self,
        tenant_id: str,
        review_id: str,
        expected_version: int,
        new_status: ReviewStatus,
        new_assigned_to: Optional[str],
        decision: ReviewDecision,
        revision: Optional[ReviewRevision] = None,
        audit_event_rationale: str = "",
        request_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[ReviewItem, ReviewDecision, AuditEvent]:
        """
        Atomically commit status transition, decision record, revision (if any),
        and append-only audit event in a single database transaction.
        Enforces optimistic concurrency via expected_version.
        """
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()

        try:
            with conn:
                # 1. Idempotency replay check
                if idempotency_key:
                    cached = conn.execute(
                        """
                        SELECT * FROM review_decisions
                        WHERE tenant_id = ? AND review_id = ? AND idempotency_key = ?
                        """,
                        (tenant_id, review_id, idempotency_key),
                    ).fetchone()
                    if cached:
                        cached_dec = self._row_to_decision(cached)
                        item = self.get_review(tenant_id, review_id)
                        last_event = conn.execute(
                            """
                            SELECT * FROM review_audit_events
                            WHERE review_id = ? ORDER BY sequence DESC LIMIT 1
                            """,
                            (review_id,),
                        ).fetchone()
                        audit_ev = (
                            self._row_to_audit_event(last_event)
                            if last_event
                            else AuditEvent(
                                event_id="cached",
                                review_id=review_id,
                                sequence=1,
                                tenant_id=tenant_id,
                                actor_id=cached_dec.actor_id,
                                action=cached_dec.action,
                                previous_status=cached_dec.from_status,
                                new_status=cached_dec.to_status,
                                previous_version=cached_dec.version_reviewed,
                                new_version=cached_dec.version_reviewed,
                                rationale=cached_dec.rationale,
                                timestamp=cached_dec.created_at,
                            )
                        )
                        return item, cached_dec, audit_ev

                # 2. Concurrency verification and item update
                curr_item_row = conn.execute(
                    "SELECT * FROM review_items WHERE tenant_id = ? AND review_id = ?",
                    (tenant_id, review_id),
                ).fetchone()

                if not curr_item_row:
                    raise ReviewNotFoundError(f"Review item '{review_id}' not found for tenant '{tenant_id}'")

                curr_version = curr_item_row["version"] if isinstance(curr_item_row, sqlite3.Row) else curr_item_row[6]
                if curr_version != expected_version:
                    raise StaleReviewVersionError(
                        f"Stale review version: expected {expected_version}, but current version is {curr_version}"
                    )

                new_version = curr_version + 1
                rev_id = revision.revision_id if revision else (
                    curr_item_row["current_revision_id"] if isinstance(curr_item_row, sqlite3.Row) else curr_item_row[9]
                )

                update_cursor = conn.execute(
                    """
                    UPDATE review_items
                    SET status = ?, version = ?, assigned_to = ?,
                        current_revision_id = ?, updated_at = ?
                    WHERE tenant_id = ? AND review_id = ? AND version = ?
                    """,
                    (
                        str(new_status),
                        new_version,
                        new_assigned_to,
                        rev_id,
                        now,
                        tenant_id,
                        review_id,
                        expected_version,
                    ),
                )

                if update_cursor.rowcount == 0:
                    raise StaleReviewVersionError("Concurrent update detected; review version was modified.")

                # 3. Insert revision if provided
                if revision:
                    val_json = json.dumps(revision.corrected_value)
                    conn.execute(
                        """
                        INSERT INTO review_revisions (
                            revision_id, review_id, tenant_id, actor_id,
                            version, corrected_value_json, corrected_type,
                            unit, evidence_quote, rationale, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            revision.revision_id,
                            review_id,
                            tenant_id,
                            revision.actor_id,
                            revision.version,
                            val_json,
                            revision.corrected_type,
                            revision.unit,
                            revision.evidence_quote,
                            revision.rationale,
                            now,
                        ),
                    )

                # 4. Insert decision record
                conn.execute(
                    """
                    INSERT INTO review_decisions (
                        decision_id, review_id, tenant_id, actor_id,
                        action, from_status, to_status, version_reviewed,
                        rationale, evidence_quote, idempotency_key, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        decision.decision_id,
                        review_id,
                        tenant_id,
                        decision.actor_id,
                        str(decision.action),
                        str(decision.from_status),
                        str(decision.to_status),
                        decision.version_reviewed,
                        decision.rationale,
                        decision.evidence_quote,
                        idempotency_key,
                        now,
                    ),
                )

                # 5. Insert ordered audit event
                seq_row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM review_audit_events WHERE review_id = ?",
                    (review_id,),
                ).fetchone()
                next_seq = seq_row[0]

                event_id = f"evt-{uuid.uuid4().hex}"
                conn.execute(
                    """
                    INSERT INTO review_audit_events (
                        event_id, review_id, sequence, tenant_id, actor_id,
                        action, previous_status, new_status, previous_version,
                        new_version, revision_id, rationale, request_id, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        review_id,
                        next_seq,
                        tenant_id,
                        decision.actor_id,
                        str(decision.action),
                        str(decision.from_status),
                        str(new_status),
                        expected_version,
                        new_version,
                        revision.revision_id if revision else None,
                        audit_event_rationale or decision.rationale,
                        request_id,
                        now,
                    ),
                )

                # Re-fetch updated review item
                updated_row = conn.execute(
                    "SELECT * FROM review_items WHERE review_id = ?",
                    (review_id,),
                ).fetchone()
                updated_item = self._row_to_review_item(updated_row)

                audit_ev = AuditEvent(
                    event_id=event_id,
                    review_id=review_id,
                    sequence=next_seq,
                    tenant_id=tenant_id,
                    actor_id=decision.actor_id,
                    action=decision.action,
                    previous_status=decision.from_status,
                    new_status=new_status,
                    previous_version=expected_version,
                    new_version=new_version,
                    rationale=audit_event_rationale or decision.rationale,
                    revision_id=revision.revision_id if revision else None,
                    request_id=request_id,
                    timestamp=now,
                )

                return updated_item, decision, audit_ev
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_audit_history(self, tenant_id: str, review_id: str) -> List[AuditEvent]:
        """Fetch ordered audit event history for a review item."""
        conn = self._get_connection()
        try:
            # Verify tenant ownership
            item = self.get_review(tenant_id, review_id)
            if not item:
                return []

            rows = conn.execute(
                """
                SELECT * FROM review_audit_events
                WHERE review_id = ?
                ORDER BY sequence ASC
                """,
                (review_id,),
            ).fetchall()
            return [self._row_to_audit_event(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def record_feedback(self, tenant_id: str, feedback: ReviewFeedback) -> str:
        """Persist structured review evaluation feedback."""
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO review_feedback (
                        feedback_id, tenant_id, review_id, candidate_id,
                        category, reviewer_id, notes, corrected_value_reference,
                        schema_version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback.feedback_id,
                        tenant_id,
                        feedback.review_id,
                        feedback.candidate_id,
                        str(feedback.category),
                        feedback.reviewer_id,
                        feedback.notes,
                        feedback.corrected_value_reference,
                        feedback.schema_version,
                        now,
                    ),
                )
            return feedback.feedback_id
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def list_feedback(
        self,
        tenant_id: str,
        review_id: Optional[str] = None,
    ) -> List[ReviewFeedback]:
        """List feedback records scoped to tenant."""
        conn = self._get_connection()
        try:
            if review_id:
                rows = conn.execute(
                    """
                    SELECT * FROM review_feedback
                    WHERE tenant_id = ? AND review_id = ?
                    ORDER BY created_at DESC
                    """,
                    (tenant_id, review_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM review_feedback
                    WHERE tenant_id = ?
                    ORDER BY created_at DESC
                    """,
                    (tenant_id,),
                ).fetchall()
            return [self._row_to_feedback(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_approved_facts(
        self,
        tenant_id: str,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve approved facts for downstream report generation.
        Only items in 'approved' or 'corrected' status are returned.
        Pending or rejected items are strictly excluded.
        """
        conn = self._get_connection()
        try:
            query = """
                SELECT r.*, rev.corrected_value_json, rev.corrected_type, rev.unit as rev_unit
                FROM review_items r
                LEFT JOIN review_revisions rev ON r.current_revision_id = rev.revision_id
                WHERE r.tenant_id = ? AND r.candidate_type = 'fact'
                  AND r.status IN ('approved', 'corrected')
            """
            params: List[Any] = [tenant_id]
            if document_id:
                query += " AND r.document_id = ?"
                params.append(document_id)

            rows = conn.execute(query, params).fetchall()
            approved_list: List[Dict[str, Any]] = []

            for r in rows:
                base_data = json.loads(r["candidate_data_json"])
                if r["status"] == str(ReviewStatus.CORRECTED) and r["corrected_value_json"]:
                    base_data["value"] = json.loads(r["corrected_value_json"])
                    base_data["value_type"] = r["corrected_type"]
                    if r["rev_unit"]:
                        base_data["unit"] = r["rev_unit"]
                    base_data["is_corrected"] = True
                else:
                    base_data["is_corrected"] = False

                base_data["review_status"] = r["status"]
                base_data["reviewed_version"] = r["version"]
                approved_list.append(base_data)

            return approved_list
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def _row_to_review_item(self, row: Any) -> ReviewItem:
        d = dict(row) if isinstance(row, sqlite3.Row) else {
            "review_id": row[0],
            "tenant_id": row[1],
            "candidate_id": row[2],
            "candidate_type": row[3],
            "document_id": row[4],
            "status": row[5],
            "version": row[6],
            "assigned_to": row[7],
            "candidate_data_json": row[8],
            "current_revision_id": row[9],
            "created_at": row[10],
            "updated_at": row[11],
        }
        return ReviewItem(
            review_id=d["review_id"],
            tenant_id=d["tenant_id"],
            candidate_id=d["candidate_id"],
            candidate_type=d["candidate_type"],
            document_id=d["document_id"],
            status=ReviewStatus(d["status"]),
            version=d["version"],
            assigned_to=d["assigned_to"],
            candidate_data=json.loads(d["candidate_data_json"]),
            current_revision_id=d["current_revision_id"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def _row_to_decision(self, row: Any) -> ReviewDecision:
        d = dict(row)
        return ReviewDecision(
            decision_id=d["decision_id"],
            review_id=d["review_id"],
            tenant_id=d["tenant_id"],
            actor_id=d["actor_id"],
            action=ReviewAction(d["action"]),
            from_status=ReviewStatus(d["from_status"]),
            to_status=ReviewStatus(d["to_status"]),
            version_reviewed=d["version_reviewed"],
            rationale=d["rationale"],
            evidence_quote=d.get("evidence_quote"),
            idempotency_key=d.get("idempotency_key"),
            created_at=d["created_at"],
        )

    def _row_to_audit_event(self, row: Any) -> AuditEvent:
        d = dict(row)
        return AuditEvent(
            event_id=d["event_id"],
            review_id=d["review_id"],
            sequence=d["sequence"],
            tenant_id=d["tenant_id"],
            actor_id=d["actor_id"],
            action=ReviewAction(d["action"]),
            previous_status=ReviewStatus(d["previous_status"]),
            new_status=ReviewStatus(d["new_status"]),
            previous_version=d["previous_version"],
            new_version=d["new_version"],
            revision_id=d.get("revision_id"),
            rationale=d["rationale"],
            request_id=d.get("request_id"),
            timestamp=d["timestamp"],
        )

    def _row_to_feedback(self, row: Any) -> ReviewFeedback:
        d = dict(row)
        return ReviewFeedback(
            feedback_id=d["feedback_id"],
            tenant_id=d["tenant_id"],
            review_id=d["review_id"],
            candidate_id=d["candidate_id"],
            category=FeedbackCategory(d["category"]),
            reviewer_id=d["reviewer_id"],
            notes=d.get("notes", ""),
            corrected_value_reference=d.get("corrected_value_reference"),
            schema_version=d.get("schema_version", 1),
            created_at=d["created_at"],
        )
