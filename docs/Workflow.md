# AMDI-OS Workflows

This document describes the end-to-end workflows of the Adaptive Mathematical Document Intelligence Operating System. It defines the paths of documents, queries, metadata, computational steps, and operational safety nets.

---

## 1. User Workflows

### 1.1 Document Upload Workflow

```
[User] ──upload──► [Frontend] ──POST──► [API Server]
                                          │
                                          ├──► [Storage] (S3 / Local Disk)
                                          │
                                          └──► [Queue] (Celery)
                                                     │
                                                     ▼
                                              [Worker Process]
                                                     │
                                                     ├──► [PDFLoader]
                                                     ├──► [OCR] (scanned docs)
                                                     ├──► [LayoutDetector]
                                                     └──► [MetadataExtractor]
                                                             │
                                                             ▼
                                                      [Document Object]
                                                             │
                                                             ▼
                                                     [Response: doc_id]
```

### 1.2 Document Query Workflow

```
[User] ──query──► [Frontend] ──POST──► [API Server]
                                         │
                                         ▼
                                   [Query Parser]
                                         │
                                         ├──► [Embedding Generation]
                                         │
                                         ▼
                                  [Hybrid Retrieval]
                                   │ │ │ │ │ │ │
                                   ▼ ▼ ▼ ▼ ▼ ▼ ▼
                       ┌───────────┴─┼─┼─┼─┼─┴───────────┐
                       ▼             ▼ ▼ ▼ ▼             ▼
                      Sem           MatGeoGrTpl         Freq Recur
                       └─────────────┬─┼─┼─┼─┬───────────┘
                                     ▼
                                [RRF Fusion]
                                     │
                                     ▼
                              [Top-K Candidates]
                                     │
                                     ▼
                              [Context Builder]
                               │ │ │ │
                               ▼ ▼ ▼ ▼
                             Rank/Comp/Summ/Assemble
                               │
                               ▼
                        [Universal Export Object]
                               │
                               ▼
                         [AI Agent Connector]
                               │
                               ▼
                         [LLM Response]
                               │
                               ▼
                         [Verification Engine]
                           │ │ │ │
                           ▼ ▼ ▼ ▼
                         Cite/Fact/Conf/Halluc
                           │
                           ▼
                    [Verified Response → User]
```

### 1.3 Dashboard Workflow

```
[User] ──view──► [Frontend]
                    │
                    ├──► [UploadDashboard] ──────► GET /api/v1/documents
                    ├──► [DocumentExplorer] ─────► GET /api/v1/documents/{id}
                    ├──► [GeometryDashboard] ────► GET /api/v1/geometry/{doc_id}
                    ├──► [MatrixDashboard] ──────► GET /api/v1/matrix/{doc_id}
                    ├──► [GraphDashboard] ───────► GET /api/v1/graph/{doc_id}
                    ├──► [MemoryDashboard] ──────► GET /api/v1/memory
                    ├──► [RetrievalDashboard] ───► POST /api/v1/search
                    ├──► [AnalyticsDashboard] ───► GET /api/v1/dashboards/analytics
                    ├──► [PerformanceDashboard] ─► GET /api/v1/dashboards/performance
                    ├──► [AgentDashboard] ───────► GET /api/v1/dashboards/agents
                    └──► [SettingsDashboard] ────► GET /api/v1/dashboards/settings
```

---

## 2. Data Workflows

### 2.1 Document Ingestion Flow

```
  PDF / DOCX / PPTX / XLSX
             │
             ▼
     [File Validation]
             │
             ▼
     [OCR if scanned] (Tesseract/PaddleOCR)
             │
             ▼
     [Layout Detection] (text blocks, tables, figures)
             │
             ▼
     [Metadata Extraction] (author, date, language)
             │
             ▼
     [Document Object]
             │
             ▼
   [12 Engines in Parallel]
     ├──► [Geometry] ──────► coordinates, bounding boxes
     ├──► [Frequency] ─────► TF-IDF, BM25
     ├──► [Recurrence] ────► MinHash signatures
     ├──► [Matrix] ────────► tables, statistics
     ├──► [Template] ──────► fingerprints
     ├──► [Semantic] ──────► embeddings
     ├──► [Graph] ─────────► PageRank, communities
     ├──► [Topology] ──────► Betti numbers
     ├──► [Spectral] ──────► eigenvectors, clusters
     ├──► [Tensor] ────────► Tucker/CP/TT decomposition
     ├──► [InfoPhysics] ───► energy, gravity, fields, entropy
     └──► [Retrieval Index]─► Qdrant + Neo4j
             │
             ▼
 [Multi-Representation Doc]
             │
             ▼
      [Fusion Engine]
             │
             ▼
  [Hierarchical Memory L0-L5]
```

### 2.2 Hybrid Retrieval Flow

```
                [Query]
                   │
                   ▼
           [Query Embedding]
                   │
                   ▼
        [7 Methods in Parallel]
          ├──► [Semantic Search] ───► cosine similarity ────────┐
          ├──► [Matrix Search] ─────► SVD correlation ──────────┤
          ├──► [Geometry Search] ───► spatial k-NN ─────────────┤
          ├──► [Graph Search] ──────► PageRank cross-refs ──────┼──► [RRF Fusion]
          ├──► [Template Search] ───► Jaccard fingerprints ─────┤          │
          ├──► [Frequency Search] ──► BM25 statistical ─────────┤          ▼
          └──► [Recurrence Search] ─► LSH signatures ───────────┘    [Top-K Docs]
                                                                           │
                                                                           ▼
                                                                   [Context Builder]
                                                                     ├──► Rank
                                                                     ├──► Compress
                                                                     ├──► Summarize
                                                                     └──► Assemble (UEO)
```

### 2.3 Verification Flow

```
              [AI Response]
                    │
                    ▼
             [Parse Response]
                    │
                    ▼
          [4 Verification Checks]
            ├──► [Citation Verification]
            │      ├──► Extract citations
            │      ├──► Match against sources
            │      └──► Score: CA (Citation Accuracy)
            │
            ├──► [Fact Verification]
            │      ├──► Extract claims
            │      ├──► Match against Knowledge Base
            │      └──► Score: FA (Fact Accuracy)
            │
            ├──► [Hallucination Detection]
            │      ├──► Uncited claims
            │      ├──► Internal contradictions
            │      ├──► Specificity paradox
            │      ├──► Entity confusion
            │      └──► Numerical inconsistencies
            │
            └──► [Confidence Scoring]
                   └──► C = α·CA + β·FA + γ·(1-HR) + δ·SR
                            │
                            ▼
                   [Verification Report]
                            │
                            ▼
             [Pass / Review / Reject Decision]
```

---

## 3. Computational Workflows

### 3.1 Engine Processing Pipeline

```
  [Document]
      │
      ▼
   [Parse] ──► [Text Extraction]
                  │
                  ├──► [Sentences]
                  ├──► [Tokens]
                  └──► [Entities]
                  │
                  ▼
          [Parallel Engines]
                  │
                  ▼
         [Result Aggregation]
                  │
                  ▼
     [Confidence-Weighted Output]
```

### 3.2 Compression Pipeline

```
  [Document Tensor T]
          │
          ▼
    [Tucker HOOI]
          │
          ▼
 [Core G + Factors U_1..U_n]
          │
          ▼
   [Truncate by Rank]
          │
          ▼
   [Compressed Tensor T̂]
          │
          ▼
 [Compression Ratio C = |T|/|T̂|]
```

### 3.3 Encryption Pipeline

```
          [Plaintext]
               │
               ▼
        [Key Generation] (AES-256)
               │
               ▼
     [AES-256-GCM Encrypt]
               │
               ▼
   [Ciphertext + Nonce + Tag]
               │
               ▼
    [Storage / Transmission]
```

---

## 4. Processing Pipelines

### 4.1 Batch Processing Pipeline

```
 [Batch of N Documents]
           │
           ▼
 [Distributed Queue (Celery)]
           │
      ┌────┼────┐
      ▼    ▼    ▼
     [Worker Pool]
      ├──► Worker 1: Document 1
      ├──► Worker 2: Document 2
      └──► Worker 3: Document 3
           │
           ▼
  [Result Aggregation]
           │
           ▼
    [Batch Report]
```

### 4.2 Streaming Pipeline

```
    [Document Stream]
           │
           ▼
       [Chunker]
           │
           ▼
   [Stream Processing]
     ├──► [Chunk 1] ──► Engine Pipeline
     ├──► [Chunk 2] ──► Engine Pipeline
     └──► [Chunk 3] ──► Engine Pipeline
           │
           ▼
   [Streaming Results]
```

---

## 5. Automation Flows

### 5.1 CI/CD Pipeline

```
         [Git Push]
             │
             ▼
  [GitHub Actions Trigger]
             │
             ▼
       [Lint + Test]
             │
             ▼ (pass)
    [Build Docker Image]
             │
             ▼
       [Trivy Scan]
             │
             ▼ (pass)
     [Push to Registry]
             │
             ▼
    [Deploy to Staging]
             │
             ▼ (smoke test pass)
   [Canary Deploy (5%..100%)]
             │
             ▼ (canary healthy)
   [Full Production Deploy]
```

### 5.2 Monitoring Pipeline

```
   [Application Metrics] (Prometheus client)
             │
             ▼
    [Prometheus Server] (scrape every 15s)
             │
             ▼
     [Alert Evaluation]
             │
             ▼ (alert triggered)
       [Alertmanager]
             │
             ▼
     [PagerDuty + Slack]
```

### 5.3 Backup Pipeline

```
       [PostgreSQL]
            │
            ▼
    [pg_dump (daily)]
            │
            ▼
   [Compress + Encrypt]
            │
            ▼
       [S3 Bucket] (versioned, lifecycle-managed)
            │
            ▼
   [90-Day Retention Policy]
```

---

## 6. Simulation Flows

### 6.1 Stress Test Flow

```
        [Load Profile]
              │
              ▼
     [Stress Test Runner]
              │
              ▼
     [Concurrent Requests]
              │
              ▼
       [Collect Metrics]
         ├──► Throughput (RPS)
         ├──► Latency (p50, p95, p99)
         └──► Error Rate
              │
              ▼
   [Identify Breaking Point]
              │
              ▼
       [Stress Report]
```

### 6.2 Ablation Study Flow

```
       [Full Pipeline]
              │
              ▼
   [Baseline Performance]
              │
              ▼
       [Disable Engine]
              │
              ▼
      [Measure Impact]
              │
              ▼
  [Contribution Analysis]
              │
              ▼
      [Ablation Report]
```

### 6.3 Robustness Test Flow

```
       [Original Input]
              │
              ▼
      [Apply Perturbation]
        ├──► NOISE
        ├──► DROPOUT
        ├──► SCRAMBLE
        ├──► TRUNCATE
        ├──► EMPTY / HUGE
        └──► SPECIAL CHARS / UNICODE
              │
              ▼
       [Run Pipeline]
              │
              ▼
    [Compare to Baseline]
              │
              ▼
      [Robustness Score]
```

---

## 7. Operational Workflows

### 7.1 Incident Response

```
       [Alert Triggered]
              │
              ▼
      [On-Call Notified]
              │
              ▼
           [Triage]
        ├──► Check Dashboards
        ├──► Check Log Streams
        └──► Check Metrics
              │
              ▼
         [Mitigation]
        ├──► Rollback Deployment
        ├──► Scale Resources
        └──► Apply Hotfix
              │
              ▼
        [Post-Mortem]
```

### 7.2 Capacity Scaling

```
 [Capacity Threshold Reached (80%)]
                 │
                 ▼
      [Predict Future Demand]
                 │
                 ▼
   [Scale EKS API/Worker Pods (HPA)]
                 │
                 ▼
   [Scale DB Replicas (if read-heavy)]
                 │
                 ▼
     [Verify Health/Throughput]
```

### 7.3 Database Failover

```
      [Primary DB Outage]
                 │
                 ▼
    [Detect Outage (Sentinel/HA)]
                 │
                 ▼
   [Promote Replica to Primary]
                 │
                 ▼
   [Update API Router Config]
                 │
                 ▼
   [Verify Read/Write Capability]
```

### 7.4 Backup and Restore

```
     [Scheduled Cron Trigger]
                 │
                 ▼
       [pg_dump / Snapshot]
                 │
                 ▼
     [Encrypt Backup (AES-256)]
                 │
                 ▼
       [Upload to S3 Archive]
                 │
                 ▼
       [Validate Integrity]
```