import os
import sys
from pathlib import Path
import pytest
import numpy as np

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.analytics import (
    AnalyticsEngine,
    cosine_similarity,
    compute_centroid,
    SimilaritySearcher,
    KnowledgeGraph,
    TrendAnalyzer,
    BehaviorAnalyticsManager,
    CostOptimizer,
)


def test_similarity_basics():
    # 1. Cosine similarity
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    v3 = np.array([1.0, 1.0, 0.0])
    
    assert cosine_similarity(v1, v2) == 0.0
    assert cosine_similarity(v1, v1) == 1.0
    assert cosine_similarity(v1, v3) == pytest.approx(0.70710678)
    
    # Empty vectors fallback
    assert cosine_similarity(v1, np.array([0.0, 0.0, 0.0])) == 0.0

    # 2. Centroid calculation
    embeddings = [
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
    ]
    centroid = compute_centroid(embeddings)
    assert centroid == [4.0, 5.0, 6.0]

    with pytest.raises(ValueError):
        compute_centroid([])


def test_similarity_searcher():
    searcher = SimilaritySearcher()
    
    searcher.add_document("doc1", [1.0, 0.0, 0.0], {"title": "Doc 1"})
    searcher.add_document("doc2", [0.9, 0.1, 0.0], {"title": "Doc 2"})
    searcher.add_document("doc3", [0.0, 1.0, 0.0], {"title": "Doc 3"})
    
    # Search by vector
    results = searcher.search_by_vector([1.0, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0][0] == "doc1"
    assert results[0][1] == pytest.approx(1.0)
    assert results[1][0] == "doc2"
    assert results[1][1] == pytest.approx(0.9938837)
    assert results[0][2] == {"title": "Doc 1"}

    # Search by document
    results_doc = searcher.search_by_document("doc1", top_k=2)
    assert len(results_doc) == 2
    assert results_doc[0][0] == "doc2"
    
    # Remove document
    assert searcher.remove_document("doc3") is True
    assert searcher.remove_document("doc3") is False
    assert len(searcher.search_by_vector([0.0, 1.0, 0.0], top_k=10)) == 2


def test_similarity_clustering():
    searcher = SimilaritySearcher()
    searcher.add_document("doc1", [1.0, 0.0, 0.0])
    searcher.add_document("doc2", [0.95, 0.05, 0.0])
    searcher.add_document("doc3", [0.0, 1.0, 0.0])
    searcher.add_document("doc4", [0.05, 0.95, 0.0])
    searcher.add_document("doc5", [0.5, 0.5, 0.5])
    
    clusters = searcher.find_clusters(threshold=0.8)
    # Expected clusters:
    # Cluster 1: doc1, doc2
    # Cluster 2: doc3, doc4
    # Cluster 3: doc5 (independent)
    
    assert len(clusters) == 3
    flat_clusters = [set(c) for c in clusters]
    assert {"doc1", "doc2"} in flat_clusters
    assert {"doc3", "doc4"} in flat_clusters
    assert {"doc5"} in flat_clusters


def test_knowledge_graph():
    kg = KnowledgeGraph()
    kg.add_node("n1", "Node 1", "Concept", {"val": 10})
    kg.add_node("n2", "Node 2", "Concept", {"val": 20})
    kg.add_edge("n1", "n2", "RELATED_TO", weight=2.5, properties={"source": "manual"})

    # Check node details
    assert kg.nodes["n1"].label == "Node 1"
    assert kg.nodes["n1"].properties == {"val": 10}

    # Check neighbors
    neighbors_n1 = kg.get_neighbors("n1", direction="out")
    assert len(neighbors_n1) == 1
    assert neighbors_n1[0][0] == "n2"
    assert neighbors_n1[0][1].weight == 2.5

    # Check reverse adjacency
    neighbors_n2_in = kg.get_neighbors("n2", direction="in")
    assert len(neighbors_n2_in) == 1
    assert neighbors_n2_in[0][0] == "n1"

    # Breadth-first shortest path
    kg.add_edge("n2", "n3", "NEXT")
    kg.add_edge("n3", "n4", "NEXT")
    kg.add_edge("n1", "n4", "SHORTCUT")  # n1 -> n4 directly
    
    path = kg.get_shortest_path("n1", "n4")
    assert path == ["n1", "n4"]

    # Delete shortcut and search path
    del kg.adjacency["n1"]["n4"]
    del kg.in_adjacency["n4"]["n1"]
    path2 = kg.get_shortest_path("n1", "n4")
    assert path2 == ["n1", "n2", "n3", "n4"]

    # Degree centrality
    centrality = kg.get_degree_centrality()
    # Nodes: n1, n2, n3, n4. N=4. Degree:
    # n1: degree=1 (n2)
    # n2: degree=2 (n1, n3)
    # n3: degree=2 (n2, n4)
    # n4: degree=1 (n3)
    # normalized: degree / 3
    assert centrality["n1"] == pytest.approx(1/3)
    assert centrality["n2"] == pytest.approx(2/3)

    # Subgraph
    sub = kg.get_subgraph_around_node("n2", depth=1)
    # Nodes in depth 1 from n2 are: n1, n2, n3
    sub_node_ids = {n["id"] for n in sub["nodes"]}
    assert sub_node_ids == {"n1", "n2", "n3"}
    assert len(sub["edges"]) == 2  # n1->n2, n2->n3


def test_trend_analyzer():
    # Moving averages
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    
    sma = TrendAnalyzer.simple_moving_average(data, window=2)
    assert sma == [10.0, 15.0, 25.0, 35.0, 45.0]

    ema = TrendAnalyzer.exponential_moving_average(data, window=2)
    # alpha = 2 / 3 = 0.6666...
    # ema[0] = 10.0
    # ema[1] = 0.666*20 + 0.333*10 = 16.666
    assert ema[0] == 10.0
    assert ema[1] == pytest.approx(16.66666667)

    # Linear Trend Fitting
    # y = 2x + 5
    timestamps = [1.0, 2.0, 3.0, 4.0, 5.0]
    values = [7.0, 9.0, 11.0, 13.0, 15.0]
    
    fit = TrendAnalyzer.fit_linear_trend(timestamps, values)
    assert fit["slope"] == pytest.approx(2.0)
    assert fit["intercept"] == pytest.approx(5.0)
    assert fit["r_squared"] == pytest.approx(1.0)
    assert fit["direction"] == 1.0  # Positive slope

    # Forecast
    fc = TrendAnalyzer.forecast(timestamps, values, [6.0, 7.0])
    assert fc == pytest.approx([17.0, 19.0])


def test_user_behavior_analytics():
    manager = BehaviorAnalyticsManager()
    
    # 1. Log query
    manager.log_query("q1", "userA", "quantum physics")
    manager.log_query("q2", "userA", "relativity theory")
    manager.log_query("q3", "userB", "black holes")
    
    # 2. Log clicks
    manager.log_click("q1", "docX", rank=1)
    manager.log_click("q2", "docY", rank=3)
    # q3 has no clicks

    # CTR
    # Overall: 2 queries with clicks out of 3 total = 2/3
    # userA: 2 with clicks out of 2 total = 1.0
    # userB: 0 with clicks out of 1 total = 0.0
    assert manager.calculate_ctr() == pytest.approx(2/3)
    assert manager.calculate_ctr("userA") == 1.0
    assert manager.calculate_ctr("userB") == 0.0

    # MRR
    # Recip ranks: q1: 1/1 = 1.0, q2: 1/3 = 0.3333, q3: 0.0
    # Overall: (1.0 + 0.3333 + 0.0) / 3 = 0.4444...
    assert manager.calculate_mrr() == pytest.approx(0.44444444)

    # Session timing
    manager.start_session("s1", "userA")
    manager.increment_activity("s1")
    manager.sessions["s1"].start_time = 1000.0
    manager.sessions["s1"].end_time = 1200.0  # 200 seconds duration

    assert manager.get_average_session_duration("userA") == 200.0

    # User Profile
    profile = manager.get_user_profile("userA")
    assert profile["total_queries"] == 2
    assert profile["click_through_rate"] == 1.0
    assert profile["average_session_duration_sec"] == 200.0


def test_cost_optimizer():
    optimizer = CostOptimizer()
    
    # Log some queries
    optimizer.log_query_execution("neural search", "gpt-4", 1000, 500, 1.5)
    optimizer.log_query_execution("neural search", "gpt-4", 1000, 500, 1.2)
    optimizer.log_query_execution("neural search", "gpt-4", 1000, 500, 1.3)
    
    # Short query routed to expensive model
    optimizer.log_query_execution("hi", "gpt-4", 10, 20, 0.5)

    # Caching check
    recs = optimizer.get_all_recommendations()
    cache_recs = [r for r in recs if r["type"] == "CACHE_QUERY"]
    routing_recs = [r for r in recs if r["type"] == "MODEL_ROUTING"]

    assert len(cache_recs) == 1
    assert cache_recs[0]["repetition_count"] == 3
    assert cache_recs[0]["estimated_monthly_savings_usd"] > 0.0

    assert len(routing_recs) == 1
    assert routing_recs[0]["action"] == "Route short, simple queries to custom-slm-dense or custom-slm-quantized model."


def test_analytics_engine():
    engine = AnalyticsEngine()
    
    # Populate similarity
    engine.similarity_searcher.add_document("docA", [1.0, 0.0])
    engine.similarity_searcher.add_document("docB", [0.98, 0.2])
    
    # Log query behavior
    engine.behavior_manager.log_query("q1", "user1", "query text")
    engine.behavior_manager.log_click("q1", "docA", 1)
    
    # Log execution cost
    engine.cost_optimizer.log_query_execution("query text", "gpt-4", 100, 100, 1.0)
    # Short query to trigger model routing cost recommendation
    engine.cost_optimizer.log_query_execution("hi", "gpt-4", 10, 20, 0.5)
    
    # Build graph
    kg = engine.generate_similarity_knowledge_graph(similarity_threshold=0.9)
    assert "docA" in kg.nodes
    assert "docB" in kg.nodes
    assert len(kg.adjacency["docA"]) == 1  # Connected because similarity >= 0.9

    # Check report
    report = engine.get_corpus_health_report()
    assert report["corpus"]["total_documents"] == 2
    assert report["user_metrics"]["click_through_rate"] == 1.0
    assert report["cost_optimization"]["total_recommendations"] > 0
