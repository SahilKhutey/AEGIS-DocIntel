"""
AMDI-OS Advanced Analytics Orchestrator
=======================================

Main entrypoint for advanced analytics services. Coordinates similarity searching,
knowledge graph extraction, timeseries trend analysis, user behavior metrics,
and cost optimization recommendations.
"""

from typing import List, Dict, Tuple, Optional, Any, Union
import numpy as np

from .similarity_search import SimilaritySearcher
from .knowledge_graph import KnowledgeGraph
from .trend_analyzer import TrendAnalyzer
from .user_behavior import BehaviorAnalyticsManager
from .cost_optimizer import CostOptimizer


class AnalyticsEngine:
    """
    Unified manager orchestrating all AMDI-OS Advanced Analytics components.
    """
    def __init__(self):
        self.similarity_searcher = SimilaritySearcher()
        self.knowledge_graph = KnowledgeGraph()
        self.behavior_manager = BehaviorAnalyticsManager()
        self.cost_optimizer = CostOptimizer()

    def generate_similarity_knowledge_graph(self, similarity_threshold: float = 0.7) -> KnowledgeGraph:
        """
        Dynamically constructs a KnowledgeGraph based on document similarity clusters.
        Creates similarity nodes and edges between documents that are closely related.
        """
        # Ensure all document nodes exist in the graph
        for doc_id in self.similarity_searcher.corpus.keys():
            self.knowledge_graph.add_node(
                node_id=doc_id,
                label=doc_id,
                node_type="Document",
                properties=self.similarity_searcher.metadata.get(doc_id, {})
            )

        # Compute pairwise similarities and add edges
        doc_ids = list(self.similarity_searcher.corpus.keys())
        n = len(doc_ids)
        for i in range(n):
            for j in range(i + 1, n):
                d1, d2 = doc_ids[i], doc_ids[j]
                sim = float(np.dot(self.similarity_searcher.corpus[d1], self.similarity_searcher.corpus[d2]) / (
                    np.linalg.norm(self.similarity_searcher.corpus[d1]) * np.linalg.norm(self.similarity_searcher.corpus[d2])
                ))
                if sim >= similarity_threshold:
                    self.knowledge_graph.add_edge(
                        source=d1,
                        target=d2,
                        rel_type="SIMILAR_TO",
                        weight=sim,
                        properties={"similarity": sim}
                    )
        return self.knowledge_graph

    def get_corpus_health_report(self) -> Dict[str, Any]:
        """
        Runs comprehensive analytics on corpus, query usage, and behavioral indicators.
        """
        total_docs = len(self.similarity_searcher.corpus)
        recs = self.cost_optimizer.get_all_recommendations()
        
        # Calculate overall CTR and MRR
        ctr = self.behavior_manager.calculate_ctr()
        mrr = self.behavior_manager.calculate_mrr()
        
        # Graph density estimation: E / (V * (V - 1)) for directed graphs
        nodes_count = len(self.knowledge_graph.nodes)
        edges_count = sum(len(adj) for adj in self.knowledge_graph.adjacency.values())
        graph_density = 0.0
        if nodes_count > 1:
            graph_density = edges_count / (nodes_count * (nodes_count - 1))

        return {
            "corpus": {
                "total_documents": total_docs,
                "graph_nodes": nodes_count,
                "graph_edges": edges_count,
                "graph_density": graph_density
            },
            "user_metrics": {
                "click_through_rate": ctr,
                "mean_reciprocal_rank": mrr,
            },
            "cost_optimization": {
                "total_recommendations": len(recs),
                "potential_monthly_savings_usd": sum(r.get("estimated_monthly_savings_usd", 0.0) for r in recs),
                "details": recs
            }
        }
