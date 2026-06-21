# AMDI-OS Stress Test Report

**Date:** 2026-01-14
**Test Window:** 24 Hours (Soak Test) + Concurrency Ramp-Up
**Environment:** Kubernetes Cluster (3 Node pool, 16 vCPU / 64 GB per node)

---

## 1. Concurrency Ramping Profile

We tested system throughput and latency by ramping up simulated concurrent users from 1 to 500.

### Results Table

| Concurrency | Requests/sec (RPS) | p90 Latency (ms) | p99 Latency (ms) | Error Rate (%) |
|-------------|--------------------|------------------|------------------|----------------|
| 1           | 5                  | 110              | 200              | 0.00%          |
| 10          | 45                 | 240              | 500              | 0.00%          |
| 50          | 180                | 650              | 1,200            | 0.10%          |
| 100         | 320                | 1,100            | 2,500            | 0.30%          |
| 200         | 480                | 2,400            | 5,000            | 0.80%          |
| 500         | 650                | 5,800            | 12,000           | 2.50%          |

### Findings
* **Optimal Operating Range:** Concurrency under 200 users maintains p99 latencies within target budgets (< 5.0s).
* **Saturation Point:** At ~500 concurrent users, throughput plateaus at 650 RPS due to CPU starvation on worker nodes running mathematical parsing engines.

---

## 2. 24-Hour Soak Test

The soak test assessed memory leakage, connection pooling degradation, and storage fragmentation over a sustained 24-hour window at 5 RPS.

* **Total Transactions Served:** 432,000 queries
* **Average Latency:** 2.3s
* **p99 Latency stability:** 5.8s ± 0.3s
* **Sustained Error Rate:** 0.02% (mostly transient third-party API issues)
* **Memory Footprint Trend:** Peak memory usage rose from 2.1 GB to 2.15 GB within the first hour and remained flat, confirming no active memory leaks.

---

## 3. Database & Cache Load Performance

* **PostgreSQL (Connection Pool):** Connections stabilized at 45 active, with query times averaging 8ms.
* **Redis (L1 Cache):** Hit rate remained stable at 78.4% during repeating tests. Read latency p95: 1.2ms.
* **Qdrant (Vector Store):** Search operations maintained < 15ms latency under peak concurrent loads.
* **Neo4j (Graph Store):** Path-based lookups averaged 24ms.
