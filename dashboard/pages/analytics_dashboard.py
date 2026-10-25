"""
Analytics Dashboard
====================

Cross-document analytics and insights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TopicCluster:
    """A topic cluster discovered across documents."""

    cluster_id: int
    label: str
    document_count: int
    keywords: List[str] = field(default_factory=list)
    size: int = 0

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "document_count": self.document_count,
            "keywords": self.keywords,
            "size": self.size,
        }


@dataclass
class AnalyticsViewData:
    """Analytics dashboard data."""

    total_documents: int = 0
    total_size_bytes: int = 0
    total_pages: int = 0
    document_types: Dict[str, int] = field(default_factory=dict)
    top_keywords: List[Dict[str, Any]] = field(default_factory=list)
    topic_clusters: List[TopicCluster] = field(default_factory=list)
    upload_timeline: List[Dict[str, Any]] = field(default_factory=list)
    processing_throughput: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_documents": self.total_documents,
            "total_size_bytes": self.total_size_bytes,
            "total_pages": self.total_pages,
            "document_types": self.document_types,
            "top_keywords": self.top_keywords,
            "topic_clusters": [tc.to_dict() for tc in self.topic_clusters],
            "upload_timeline": self.upload_timeline,
            "processing_throughput": self.processing_throughput,
        }


class AnalyticsDashboard:
    """Analytics dashboard backend API."""

    def __init__(self, document_explorer: Any) -> None:
        self.explorer = document_explorer

    def get_view(self) -> AnalyticsViewData:
        stats = self.explorer.get_stats()
        view = AnalyticsViewData(
            total_documents=stats["total_documents"],
            total_size_bytes=stats["total_size_bytes"],
            total_pages=stats["total_pages"],
            document_types=stats["by_type"],
        )
        # upload timeline (group by date)
        from collections import Counter
        date_counts: Counter = Counter()
        for doc in self.explorer.documents.values():
            date = doc.uploaded_at[:10] if doc.uploaded_at else "unknown"
            date_counts[date] += 1
        view.upload_timeline = [
            {"date": d, "count": c}
            for d, c in sorted(date_counts.items())
        ]
        return view

    def get_top_keywords(self, top_k: int = 20) -> List[Dict[str, Any]]:
        """Aggregate keywords across documents (placeholder TF-IDF)."""
        from collections import Counter
        all_words: Counter = Counter()
        for doc in self.explorer.documents.values():
            words = doc.name.lower().split()
            for w in words:
                if len(w) > 3:
                    all_words[w] += 1
        return [
            {"keyword": w, "count": c}
            for w, c in all_words.most_common(top_k)
        ]
