import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Configure Python path to find ui.src.pages and amdi-os source modules
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "amdi-os"))


def test_dashboard_package_imports():
    """Verify that the ui.src.pages package and all its models can be imported."""
    from ui.src.pages import (
        UploadDashboard,
        UploadPageData,
        DocumentExplorer,
        DocumentSummary,
        GeometryDashboard,
        GeometryViewData,
        MatrixDashboard,
        MatrixViewData,
        GraphDashboard,
        GraphViewData,
        MemoryDashboard,
        MemoryViewData,
        RetrievalDashboard,
        RetrievalViewData,
        AnalyticsDashboard,
        AnalyticsViewData,
        PerformanceDashboard,
        PerformanceViewData,
        AgentDashboard,
        AgentViewData,
        SettingsDashboard,
        SettingsData,
    )
    assert True


def test_upload_dashboard():
    """Test UploadDashboard controller and model operations."""
    from ui.src.pages.upload_dashboard import UploadDashboard, UploadStatus

    db = UploadDashboard()
    
    # Test Create
    item = db.create_upload("test.pdf", 1024, "pdf")
    assert item.upload_id is not None
    assert item.filename == "test.pdf"
    assert item.status == UploadStatus.PENDING

    # Test Update Progress
    db.update_progress(item.upload_id, 0.5, UploadStatus.UPLOADING)
    assert item.progress == 0.5
    assert item.status == UploadStatus.UPLOADING

    # Test Complete
    db.complete_upload(item.upload_id, "doc-123")
    assert item.status == UploadStatus.COMPLETED
    assert item.progress == 1.0
    assert item.document_id == "doc-123"

    # Test Fail
    fail_item = db.create_upload("fail.pdf", 2048, "pdf")
    db.fail_upload(fail_item.upload_id, "Malformed PDF")
    assert fail_item.status == UploadStatus.FAILED
    assert fail_item.error_message == "Malformed PDF"

    # Page Data
    data = db.get_page_data()
    assert data.total_uploaded == 2
    assert len(data.recent_uploads) == 2
    assert data.success_rate == 0.5
    assert data.to_dict()["success_rate"] == 0.5


def test_document_explorer():
    """Test DocumentExplorer controller operations."""
    from ui.src.pages.document_explorer import DocumentExplorer

    db = DocumentExplorer()
    db.add_document("doc-1", "spec.pdf", "pdf", 2048, page_count=2, tags=["spec", "amdi"])
    db.add_document("doc-2", "draft.docx", "docx", 4096, page_count=5, tags=["draft"])

    db.mark_processed("doc-1", {"ocr": True, "layout": True})
    
    # Verify processing status
    docs = db.list_documents(processed_only=True)
    assert len(docs) == 1
    assert docs[0].document_id == "doc-1"
    assert docs[0].processed is True

    # Search
    results = db.search("draft")
    assert len(results) == 1
    assert results[0].document_id == "doc-2"

    results_tag = db.search("amdi")
    assert len(results_tag) == 1
    assert results_tag[0].document_id == "doc-1"

    # Stats
    stats = db.get_stats()
    assert stats["total_documents"] == 2
    assert stats["processed"] == 1
    assert stats["by_type"]["pdf"] == 1
    assert stats["total_size_bytes"] == 6144


def test_geometry_dashboard():
    """Test GeometryDashboard coordinate and bounding box calculations."""
    from ui.src.pages.geometry_dashboard import GeometryDashboard, BoundingBox

    db = GeometryDashboard()
    bbox1 = BoundingBox("el-1", 10.0, 20.0, 100.0, 150.0, page=1, element_type="text", confidence=0.95)
    bbox2 = BoundingBox("el-2", 15.0, 30.0, 200.0, 50.0, page=2, element_type="table", confidence=0.85)

    db.add_bounding_box("doc-1", bbox1)
    db.add_bounding_box("doc-1", bbox2)
    db.set_page_count("doc-1", 3)

    view = db.get_view("doc-1")
    assert view.page_count == 3
    assert len(view.bounding_boxes) == 2
    assert view.average_confidence == pytest.approx(0.90)
    assert view.element_type_counts["text"] == 1
    assert view.element_type_counts["table"] == 1

    # Filter page
    page_view = db.get_view("doc-1", page=2)
    assert len(page_view.bounding_boxes) == 1
    assert page_view.bounding_boxes[0].element_id == "el-2"
    assert page_view.average_confidence == 0.85


def test_matrix_dashboard():
    """Test MatrixDashboard and numerical stats calculations."""
    import numpy as np
    from ui.src.pages.matrix_dashboard import MatrixDashboard, TableSummary

    db = MatrixDashboard()
    table = TableSummary(
        table_id="tbl-1",
        document_id="doc-1",
        page=1,
        headers=["ColA", "ColB"],
        row_count=3,
        col_count=2,
        data_preview=[[1, 2], [3, 4], [5, 6]],
        statistics={"completeness": 1.0},
        completeness=0.95,
        confidence=0.98
    )

    db.add_table("doc-1", table)
    
    view = db.get_view("doc-1")
    assert view.total_rows == 3
    assert view.total_cols == 2
    assert view.average_completeness == 0.95

    # Compute statistics
    matrix = np.array([[10, 20], [30, 40]])
    stats = db.compute_statistics("tbl-1", matrix)
    assert stats["mean"] == 25.0
    assert stats["min"] == 10.0
    assert stats["max"] == 40.0
    assert stats["sum"] == 100.0


def test_graph_dashboard():
    """Test GraphDashboard node positioning and metrics."""
    from ui.src.pages.graph_dashboard import GraphDashboard, GraphNode, GraphEdge

    db = GraphDashboard()
    n1 = GraphNode("n1", "Node A", "entity", degree=2, pagerank=0.5, cluster_id=1)
    n2 = GraphNode("n2", "Node B", "entity", degree=1, pagerank=0.25, cluster_id=1)
    n3 = GraphNode("n3", "Node C", "concept", degree=1, pagerank=0.25, cluster_id=2)

    db.add_node("doc-1", n1)
    db.add_node("doc-1", n2)
    db.add_node("doc-1", n3)

    e1 = GraphEdge("n1", "n2", weight=1.5, edge_type="link")
    e2 = GraphEdge("n1", "n3", weight=0.8, edge_type="association")

    db.add_edge("doc-1", e1)
    db.add_edge("doc-1", e2)

    # Simple force directed positions check
    db.compute_layout("doc-1", iterations=10)
    view = db.get_view("doc-1")
    assert view.density == 2.0 / 3.0  # 2 * 2 / (3 * 2) = 4/6 = 2/3
    assert view.average_degree == pytest.approx(4.0 / 3.0)  # (2 + 1 + 1)/3 = 4/3
    assert view.num_clusters == 2

    # Check positions were updated
    assert view.nodes[0].x != 0.0 or view.nodes[0].y != 0.0


def test_memory_dashboard():
    """Test MemoryDashboard wrapping the Hierarchical MemoryEngine."""
    from ui.src.pages.memory_dashboard import MemoryDashboard
    
    # Mock MemoryEngine structures
    mock_stats = MagicMock()
    mock_stats.total_items = 150
    mock_stats.total_bytes = 204800
    mock_stats.cache_size = 20
    mock_stats.total_accesses = 500

    # Define level constants matching amdi-os/src/engines/memory
    try:
        from src.engines.memory import MemoryLevel
    except ImportError:
        try:
            from engines.memory import MemoryLevel
        except ImportError:
            from enum import Enum
            class DummyMemoryLevel(Enum):
                L0_RAW = 0
                L1_TEMPLATES = 1
                L2_STRUCTURES = 2
                L3_TABLES = 3
                L4_SEMANTIC = 4
                L5_SUMMARIES = 5

                @property
                def name_long(self):
                    return ["raw", "templates", "structures", "tables", "semantic", "summaries"][self.value]
            MemoryLevel = DummyMemoryLevel

    # Populate Stats and EngineMock
    mock_stats.items_per_level = {
        MemoryLevel.L0_RAW: 100,
        MemoryLevel.L4_SEMANTIC: 40,
        MemoryLevel.L5_SUMMARIES: 10
    }
    mock_stats.bytes_per_level = {
        MemoryLevel.L0_RAW: 150000,
        MemoryLevel.L4_SEMANTIC: 50000,
        MemoryLevel.L5_SUMMARIES: 4800
    }
    mock_stats.capacity_per_level = {
        MemoryLevel.L0_RAW: 1000,
        MemoryLevel.L4_SEMANTIC: 200,
        MemoryLevel.L5_SUMMARIES: 50
    }

    mock_engine = MagicMock()
    mock_engine.stats.return_value = mock_stats
    
    # Capacity bytes per level config mock
    mock_capacity = MagicMock()
    mock_capacity.capacity_bytes = 1000000
    mock_engine.memory.storage.capacity.return_value = mock_capacity

    db = MemoryDashboard(mock_engine)
    view = db.get_view()

    assert view.total_items == 150
    assert view.total_bytes == 204800
    assert len(view.levels) > 0

    heatmap = db.get_heatmap_data()
    assert "levels" in heatmap
    assert "utilization" in heatmap


def test_retrieval_dashboard():
    """Test RetrievalDashboard hybrid retrieval execute interface."""
    from ui.src.pages.retrieval_dashboard import RetrievalDashboard, RetrievalQueryRequest

    mock_ranking = MagicMock()
    mock_doc1 = MagicMock()
    mock_doc1.doc_id = "doc-abc"
    mock_doc1.fused_score = 0.95
    mock_doc1.methods_found = ["semantic", "graph"]
    mock_doc1.per_method_score = {"semantic": 0.9, "graph": 0.98}

    mock_ranking.ranked_docs = [mock_doc1]
    mock_ranking.num_docs = 250

    mock_report = MagicMock()
    mock_report.ranking = mock_ranking
    mock_report.per_method_counts = {"semantic": 150, "graph": 100}

    mock_retrieval_engine = MagicMock()
    mock_retrieval_engine.retrieve.return_value = mock_report

    db = RetrievalDashboard(mock_retrieval_engine)
    req = RetrievalQueryRequest(query_text="Machine Learning", semantic_embedding=[0.1, 0.2], top_k=5)
    
    view = db.execute(req)
    assert view.total_candidates == 250
    assert len(view.hits) == 1
    assert view.hits[0].doc_id == "doc-abc"
    assert view.hits[0].fused_score == 0.95
    assert view.per_method_counts["semantic"] == 150


def test_analytics_dashboard():
    """Test AnalyticsDashboard trends and topic clusters."""
    from ui.src.pages.analytics_dashboard import AnalyticsDashboard
    from ui.src.pages.document_explorer import DocumentSummary

    # Mock explorer
    mock_doc1 = DocumentSummary(
        document_id="doc1", name="quantum gravity paper", file_type="pdf",
        size_bytes=1000, page_count=4, uploaded_at="2026-06-01T10:00:00", processed=True
    )
    mock_doc2 = DocumentSummary(
        document_id="doc2", name="deep learning paper", file_type="pdf",
        size_bytes=2000, page_count=6, uploaded_at="2026-06-01T12:00:00", processed=True
    )

    mock_explorer = MagicMock()
    mock_explorer.get_stats.return_value = {
        "total_documents": 2, "total_size_bytes": 3000, "total_pages": 10, "by_type": {"pdf": 2}
    }
    mock_explorer.documents = {"doc1": mock_doc1, "doc2": mock_doc2}

    db = AnalyticsDashboard(mock_explorer)
    view = db.get_view()
    
    assert view.total_documents == 2
    assert view.total_size_bytes == 3000
    assert len(view.upload_timeline) == 1
    assert view.upload_timeline[0]["date"] == "2026-06-01"

    keywords = db.get_top_keywords(top_k=2)
    assert len(keywords) > 0
    # "paper" should be the most common word
    assert keywords[0]["keyword"] == "paper"


def test_performance_dashboard():
    """Test PerformanceDashboard engine metrics and percentiles."""
    from ui.src.pages.performance_dashboard import PerformanceDashboard, PerformanceTracker

    tracker = PerformanceTracker(window_size=10)
    tracker.record("semantic", 12.5, success=True)
    tracker.record("semantic", 15.0, success=True)
    tracker.record("graph", 45.0, success=False)

    db = PerformanceDashboard(tracker)
    view = db.get_view()

    # Latency percentiles check (using simple percentiles formula in performance_dashboard)
    assert len(view.engine_metrics) == 2
    # error rate is computed by averaging the engine error rates: (0% + 100%) / 2 = 50%
    assert view.error_rate == pytest.approx(0.5)
    assert view.uptime_seconds > 0.0


def test_agent_dashboard():
    """Test AgentDashboard connector requests and specifications."""
    from ui.src.pages.agent_dashboard import AgentDashboard
    
    db = AgentDashboard(default_agent="gemini")
    view = db.get_view()
    
    assert view.default_agent == "gemini"
    assert len(view.agents) > 0
    
    # Record request mock
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.usage = {"total_tokens": 150}
    mock_response.latency_ms = 450.0

    db.record_request("gemini", mock_response)
    updated_view = db.get_view()
    assert updated_view.total_requests == 1
    assert updated_view.total_tokens == 150


def test_settings_dashboard():
    """Test SettingsDashboard configuration state updates."""
    from ui.src.pages.settings_dashboard import SettingsDashboard

    db = SettingsDashboard()
    
    # Check default retrieval
    data = db.get_settings()
    assert data.system.storage_backend == "in_memory"
    
    # Update system configuration
    db.update_system_settings(storage_backend="redis://localhost:6379", cache_capacity=500)
    updated = db.get_settings()
    assert updated.system.storage_backend == "redis://localhost:6379"
    assert updated.system.cache_capacity == 500

    # Update agent configuration
    db.update_agent_settings("chatgpt", enabled=False, temperature=0.5, api_key="sk-test-key1234")
    agent_info = db.agents["chatgpt"]
    assert agent_info.enabled is False
    assert agent_info.temperature == 0.5
    assert agent_info.api_key_configured is True
    assert agent_info.api_key_masked == "*1234"
