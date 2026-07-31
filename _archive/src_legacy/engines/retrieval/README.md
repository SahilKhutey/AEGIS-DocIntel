# AMDI-OS Hybrid Retrieval Engine

Combines seven specialized retrieval strategies across all AMDI-OS engines (semantic, matrix, geometry, graph, template, frequency, and recurrence) and aggregates their results using rank fusion algorithms.

## Retrieval Strategies

1. **Semantic Search** — Embedding-based dense similarity search (Cosine, Dot product, Euclidean).
2. **Matrix Search** — Tabular row/column cosine matches, SVD projection, and cell-value search.
3. **Geometry Search** — Layout spatial proximity search using k-NN, radius queries, and bounding boxes.
4. **Graph Search** — traversal queries using BFS, Personalized PageRank, and shortest paths.
5. **Template Search** — Signature/fingerprint matching via Hamming, Jaccard, or Cosine metrics.
6. **Frequency Search** — Token keyword search using BM25 and TF-IDF models.
7. **Recurrence Search** — Locality-Sensitive Hashing (LSH) and MinHash Jaccard similarity near-duplicate detection.

## Fusion Algorithms

* **RRF (Reciprocal Rank Fusion)**: Combines document ranks across search methods:
  \[RRF(d) = \sum_{m} \frac{w_m}{k + \text{rank}_m(d)}\]
* **Borda Count**: Aggregates points based on inverted position in each candidate list.
* **Weighted Sum**: Sums normalized candidate relevance scores across engines.
* **Condorcet Fusion**: Pairwise Copeland preference voting.

## Directory Structure

* `__init__.py`: Package entry point exposing all engine symbols. Implements a polymorphic `HybridRetriever` factory to maintain backwards compatibility with legacy workflows.
* `retrieval_engine.py`: Orchestrator coordinating all retrieval steps and generating reports.
* `hybrid_retrieval.py`: Main hybrid retriever coordinating the 7 search tier indices.
* `semantic_search.py`: Embedding search module.
* `matrix_search.py`: Tabular/matrix search module.
* `geometry_search.py`: Spatial layout coordinate search module.
* `graph_search.py`: Graph personalized PageRank and BFS traversals.
* `template_search.py`: Fingerprint template matcher.
* `frequency_search.py`: Term frequency BM25 search.
* `recurrence_search.py`: MinHash and LSH near-duplicate detector.
* `ranker.py`: Fusion ranker implementing RRF, Borda, Weighted Sum, and Condorcet algorithms.
* `exceptions.py`: Custom exceptions.
