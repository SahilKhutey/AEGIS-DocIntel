# AMDI-OS Hierarchical Memory Engine

Six-level hierarchical memory system for AEGIS-AMDI-OS that provides structured tiers for storing, caching, promoting, evicting, and retrieving document structures and semantic data.

## Memory Levels

* **L0 Raw** (priority 0) — Original document content (bytes/strings). Disk-backed.
* **L1 Templates** (priority 1) — Extracted document layout templates & fingerprints.
* **L2 Structures** (priority 2) — Graph, topological, and tensor structural data.
* **L3 Tables** (priority 3) — Tabular structures and matrix representations.
* **L4 Semantic** (priority 4) — Dense embedding vectors.
* **L5 Summaries** (priority 5) — Compressed abstractive/extractive summaries. Fastest memory.

## Mathematical Foundation

### Promotion Score
Items are promoted up the hierarchy based on read frequency, importance, and recency:
\[P(v) = \alpha \cdot \text{frequency}(v) + \beta \cdot \text{importance}(v) + \gamma \cdot \text{recency}(v)\]
If \(P(v) \geq \theta_p(\text{level})\), the item is promoted to the next level: \(\text{level} \to \text{level} + 1\).

### Eviction Score
When storage limits are reached, items with the lowest score are evicted:
\[E(v) = \alpha \cdot \text{recency}(v) + \beta \cdot \text{frequency}(v) + \gamma \cdot \text{importance}(v)\]
Items below protection thresholds (e.g., summaries and semantic indices) are protected from aggressive eviction.

### Cache Policies
Supported in-memory caches include:
- **LRU** (Least Recently Used)
- **LFU** (Least Frequently Used)
- **ARC** (Adaptive Replacement Cache) — Adaptively balances between recency and frequency lists.

## Directory Structure

* `__init__.py`: Package-level exposure.
* `memory_engine.py`: Main orchestrator coordinating all memory operations and reports.
* `hierarchical_memory.py`: L0-L5 hierarchical storage and caching manager.
* `levels.py`: Definitions of L0-L5 memory levels and metadata.
* `store.py`: Local and file-based storage manager.
* `cache.py`: Cache manager supporting LRU, LFU, and ARC.
* `promoter.py`: Promotion scoring logic.
* `evictor.py`: Eviction policies and sizing.
* `retriever.py`: Multi-level and hybrid semantic query retrieval.
* `access_tracker.py`: Tracks read/write activity stats per item.
* `exceptions.py`: Custom memory exceptions.
