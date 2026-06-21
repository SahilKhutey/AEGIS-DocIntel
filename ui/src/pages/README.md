# AMDI-OS Dashboard Pages

This directory contains python-based backend API contracts and data serialization structures for the 11 dashboard pages of the AMDI-OS Web UI:

1. **Upload Dashboard** (`upload_dashboard.py`): Ingestion tracking, progress updates, validation.
2. **Document Explorer** (`document_explorer.py`): Listing, searching, and summary stats of ingested docs.
3. **Geometry Dashboard** (`geometry_dashboard.py`): Bounding boxes, confidence metrics, coordinate views.
4. **Matrix Dashboard** (`matrix_dashboard.py`): Table previews and matrix computation statistics.
5. **Graph Dashboard** (`graph_dashboard.py`): Nodes, edges, centrality, clusters, PageRank.
6. **Memory Dashboard** (`memory_dashboard.py`): Tiered storage (L0-L5) capacity, utilization, promotions.
7. **Retrieval Dashboard** (`retrieval_dashboard.py`): Hybrid queries and latency analytics.
8. **Analytics Dashboard** (`analytics_dashboard.py`): Topic clusters and timeline trends.
9. **Performance Dashboard** (`performance_dashboard.py`): Engine latencies, CPU/RAM, throughput metrics.
10. **Agent Dashboard** (`agent_dashboard.py`): AI provider connectors configured, requests, token budgets.
11. **Settings Dashboard** (`settings_dashboard.py`): Global paths, keys, capacities, policies.
