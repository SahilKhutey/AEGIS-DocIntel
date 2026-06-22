"""
AMDI-OS Advanced Analytics: User Behavior Analytics
===================================================

Aggregates user search queries, click logs, session durations, and computes
performance ratios like Click-Through Rate (CTR) and Mean Reciprocal Rank (MRR).
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import time


@dataclass
class SearchQueryLog:
    query_id: str
    user_id: str
    query_text: str
    timestamp: float
    clicked_doc_ids: List[str] = field(default_factory=list)
    clicked_ranks: List[int] = field(default_factory=list)  # 1-based ranks


@dataclass
class SessionLog:
    session_id: str
    user_id: str
    start_time: float
    end_time: Optional[float] = None
    activity_count: int = 0


class BehaviorAnalyticsManager:
    """
    Ingests and analyzes user interactions to build search quality metrics.
    """
    def __init__(self):
        self.queries: Dict[str, SearchQueryLog] = {}
        self.sessions: Dict[str, SessionLog] = {}
        # user_id -> list of session_ids
        self.user_sessions: Dict[str, List[str]] = {}

    def log_query(self, query_id: str, user_id: str, query_text: str) -> SearchQueryLog:
        """
        Logs a new user search query.
        """
        log = SearchQueryLog(
            query_id=query_id,
            user_id=user_id,
            query_text=query_text,
            timestamp=time.time()
        )
        self.queries[query_id] = log
        return log

    def log_click(self, query_id: str, doc_id: str, rank: int) -> bool:
        """
        Logs a user clicking a document result for a given query.
        """
        if query_id in self.queries:
            log = self.queries[query_id]
            log.clicked_doc_ids.append(doc_id)
            log.clicked_ranks.append(rank)
            return True
        return False

    def start_session(self, session_id: str, user_id: str) -> SessionLog:
        """
        Begins a new user session.
        """
        session = SessionLog(
            session_id=session_id,
            user_id=user_id,
            start_time=time.time()
        )
        self.sessions[session_id] = session
        self.user_sessions.setdefault(user_id, []).append(session_id)
        return session

    def end_session(self, session_id: str) -> bool:
        """
        Ends an active user session.
        """
        if session_id in self.sessions:
            self.sessions[session_id].end_time = time.time()
            return True
        return False

    def increment_activity(self, session_id: str) -> bool:
        """
        Tracks general interaction activity within a session.
        """
        if session_id in self.sessions:
            self.sessions[session_id].activity_count += 1
            return True
        return False

    def calculate_ctr(self, user_id: Optional[str] = None) -> float:
        """
        Calculates the Click-Through Rate (CTR) - fraction of queries with at least one click.
        """
        filtered_queries = [
            q for q in self.queries.values() 
            if user_id is None or q.user_id == user_id
        ]
        if not filtered_queries:
            return 0.0

        queries_with_clicks = sum(1 for q in filtered_queries if len(q.clicked_doc_ids) > 0)
        return float(queries_with_clicks / len(filtered_queries))

    def calculate_mrr(self, user_id: Optional[str] = None) -> float:
        """
        Calculates the Mean Reciprocal Rank (MRR) of clicked search results.
        MRR = (1 / N) * sum(1 / first_clicked_rank)
        """
        filtered_queries = [
            q for q in self.queries.values() 
            if user_id is None or q.user_id == user_id
        ]
        if not filtered_queries:
            return 0.0

        reciprocal_ranks = []
        for q in filtered_queries:
            if q.clicked_ranks:
                # Use the rank of the first clicked item (rank is 1-based)
                first_rank = min(q.clicked_ranks)
                if first_rank > 0:
                    reciprocal_ranks.append(1.0 / first_rank)
                else:
                    reciprocal_ranks.append(0.0)
            else:
                # If no clicks, reciprocal rank is 0.0
                reciprocal_ranks.append(0.0)

        return float(sum(reciprocal_ranks) / len(filtered_queries))

    def get_average_session_duration(self, user_id: Optional[str] = None) -> float:
        """
        Calculates the average session duration in seconds.
        """
        filtered_sessions = [
            s for s in self.sessions.values()
            if (user_id is None or s.user_id == user_id) and s.end_time is not None
        ]
        if not filtered_sessions:
            return 0.0

        durations = [s.end_time - s.start_time for s in filtered_sessions]
        return float(sum(durations) / len(durations))

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Generates a summary profile of a user's search and session behavior.
        """
        user_queries = [q for q in self.queries.values() if q.user_id == user_id]
        user_sess_ids = self.user_sessions.get(user_id, [])
        user_sess = [self.sessions[sid] for sid in user_sess_ids if sid in self.sessions]
        
        return {
            "user_id": user_id,
            "total_queries": len(user_queries),
            "total_sessions": len(user_sess),
            "click_through_rate": self.calculate_ctr(user_id),
            "mean_reciprocal_rank": self.calculate_mrr(user_id),
            "average_session_duration_sec": self.get_average_session_duration(user_id),
            "average_activities_per_session": float(sum(s.activity_count for s in user_sess) / len(user_sess)) if user_sess else 0.0
        }
