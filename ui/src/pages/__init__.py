"""
AMDI-OS Dashboard Pages
========================

11 dashboard pages for the AMDI-OS web UI.

Pages:
    - Upload Dashboard       : file ingestion & tracking
    - Document Explorer      : browse documents
    - Geometry Dashboard     : spatial coordinates
    - Matrix Dashboard       : tables / statistics
    - Graph Dashboard        : relationships, PageRank
    - Memory Dashboard       : L0-L5 hierarchy
    - Retrieval Dashboard    : hybrid search interface
    - Analytics Dashboard    : cross-document insights
    - Performance Dashboard  : engine metrics
    - Agent Dashboard        : AI connector control
    - Settings Dashboard     : system configuration

UI Framework: React + TypeScript (this module provides
backend API contracts + component skeletons).

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .upload_dashboard import UploadDashboard, UploadPageData
from .document_explorer import DocumentExplorer, DocumentSummary
from .geometry_dashboard import GeometryDashboard, GeometryViewData
from .matrix_dashboard import MatrixDashboard, MatrixViewData
from .graph_dashboard import GraphDashboard, GraphViewData
from .memory_dashboard import MemoryDashboard, MemoryViewData
from .retrieval_dashboard import RetrievalDashboard, RetrievalViewData
from .analytics_dashboard import AnalyticsDashboard, AnalyticsViewData
from .performance_dashboard import PerformanceDashboard, PerformanceViewData
from .agent_dashboard import AgentDashboard, AgentViewData
from .settings_dashboard import SettingsDashboard, SettingsData
from .math_advanced_dashboard import MathAdvancedDashboard, AdvancedMathDashboardData

__all__ = [
    "UploadDashboard",
    "UploadPageData",
    "DocumentExplorer",
    "DocumentSummary",
    "GeometryDashboard",
    "GeometryViewData",
    "MatrixDashboard",
    "MatrixViewData",
    "GraphDashboard",
    "GraphViewData",
    "MemoryDashboard",
    "MemoryViewData",
    "RetrievalDashboard",
    "RetrievalViewData",
    "AnalyticsDashboard",
    "AnalyticsViewData",
    "PerformanceDashboard",
    "PerformanceViewData",
    "AgentDashboard",
    "AgentViewData",
    "SettingsDashboard",
    "SettingsData",
    "MathAdvancedDashboard",
    "AdvancedMathDashboardData",
]

__version__ = "1.0.0"
