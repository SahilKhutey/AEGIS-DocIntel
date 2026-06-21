# AMDI-OS Architecture

This document describes the structural and layered architecture of the Adaptive Mathematical Document Intelligence Operating System.

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT                          │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                        INGESTION LAYER                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│ │   PDF    │ │   DOCX   │ │   PPTX   │ │   XLSX   │ │ Images │ │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                       NORMALIZATION LAYER                      │
│        Layout · OCR · Metadata · Language Detection            │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                  12 ENGINES LAYER (Wave 1-4)                   │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐│
│ │Geom │ │Freq │ │Recur│ │Matri│ │Tpl  │ │Sem  │ │Graph│ │Topo ││
│ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘│
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌────────────┐                         │
│ │Spec │ │Tens │ │Info │ │Retrieval   │                         │
│ └─────┘ └─────┘ └Phys │ └────────────┘                         │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                       FUSION ENGINE LAYER                      │
│    Dynamic Weighting · Ranking · Confidence · Fusion Scoring    │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                HIERARCHICAL MEMORY LAYER (L0-L5)               │
│             Store · Cache · Promote · Evict · Retrieve         │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                     HYBRID RETRIEVAL LAYER                     │
│      Semantic · Matrix · Geometry · Graph · Template ·         │
│       Frequency · Recurrence (7 methods → RRF fusion)          │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                     CONTEXT BUILDER LAYER                      │
│             Rank → Compress → Summarize → Assemble             │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                          EXPORT LAYER                          │
│        JSON · Markdown · YAML · Universal Export Object        │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                   AI AGENT CONNECTORS LAYER                    │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ │
│ │ChatGPT │ │ Gemini │ │ Claude │ │DeepSeek│ │  Qwen  │ │Local│ │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └─────┘ │
└─────────────────────────────┬──────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                       VERIFICATION LAYER                       │
│          Citation · Fact · Confidence · Hallucination          │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
                       RESPONSE → USER
```

---

## 2. Layer Architecture

### 2.1 Layered Stack

```
┌────────────────────────────────────────────────────────────────┐
│ L9 PRESENTATION    │ Dashboards (11 pages) · Reports           │
├────────────────────────────────────────────────────────────────┤
│ L8 CROSS-CUTTING   │ Security · Optimization · Validation ·     │
│                    │ Benchmarking · Monitoring · Logging       │
├────────────────────────────────────────────────────────────────┤
│ L7 VERIFICATION    │ Citation / Fact / Confidence / Halluc.    │
├────────────────────────────────────────────────────────────────┤
│ L6 CONNECTORS      │ 6 AI agents (ChatGPT / Gemini / Claude /  │
│                    │ DeepSeek / Qwen / Local)                  │
├────────────────────────────────────────────────────────────────┤
│ L5 EXPORT          │ JSON / Markdown / YAML / UEO              │
├────────────────────────────────────────────────────────────────┤
│ L4 CONTEXT         │ Rank → Compress → Summarize → Assemble    │
├────────────────────────────────────────────────────────────────┤
│ L3 RETRIEVAL       │ 7 hybrid methods + RRF fusion             │
├────────────────────────────────────────────────────────────────┤
│ L2 INTELLIGENCE    │ Fusion + Memory (L0-L5) + 12 Engines      │
├────────────────────────────────────────────────────────────────┤
│ L1 INGESTION       │ PDF / DOCX / PPTX / XLSX / OCR            │
├────────────────────────────────────────────────────────────────┤
│ L0 INFRASTRUCTURE  │ Docker / Kubernetes / Terraform / CI/CD   │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Between Layers

User → L1 Ingestion → L2 Intelligence (12 Engines) → L3 Fusion + Memory + Retrieval → L4 Context Builder → L5 Export (UEO) → L6 Connectors → L7 Verification → User

---

## 3. Microservice Architecture

For production deployment, AMDI-OS runs as independent microservices:

```
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │     API      │      │    Worker    │      │  Dashboard   │
 │  (FastAPI)   │      │   (Celery)   │      │   (React)    │
 └──────┬───────┘      └──────┬───────┘      └──────┬───────┘
        │                     │                     │
        └──────────────┬──────┴─────────────────────┘
                       │
        ┌──────────────▼─────────────────────┐
        │                                    │
 ┌──────▼──────┐        ┌───────▼──────┐     ┌──────▼──────┐
 │ PostgreSQL  │        │    Redis     │     │   Qdrant    │
 │    (RDS)    │        │ (ElastiCache)│     │  (Vector)   │
 └─────────────┘        └──────────────┘     └─────────────┘
 ┌─────────────┐        ┌──────────────┐     ┌─────────────┐
 │    Neo4j    │        │  Prometheus  │     │   Grafana   │
 │   (Graph)   │        │  (Metrics)   │     │ (Dashboard) │
 └─────────────┘        └──────────────┘     └─────────────┘
```

---

## 4. Data Flow Diagrams

### 4.1 Document Processing Flow

```
   [PDF / Files]
         │
         ▼
       [OCR] ──► [Layout Detection] ──► [Metadata Extraction]
                                              │
                                              ▼
                                      [Document Object]
                                              │
                                              ▼
                                         [12 Engines]
                                              │
                                              ▼
                                    [Multi-representation]
                                              │
                                              ▼
                                       [Fusion Engine]
                                              │
                                              ▼
                                   [Confidence Weighted Score]
                                              │
                                              ▼
                                  [Hierarchical Memory L0-L5]
                                              │
                                              ▼
                                      [Indexed Storage]
                                              │
                                              ▼
                                      [Hybrid Retrieval]
                                              │
                                              ▼
                                      [Context Builder]
                                              │
                                              ▼
                                  [Universal Export Object]
                                              │
                                              ▼
                                         [AI Agent]
                                              │
                                              ▼
                                        [Verification]
                                              │
                                              ▼
                                          [Response]
```

### 4.2 Query Flow

```
                  [User Query]
                       │
                       ▼
             [Embedding Generation]
                       │
                       ▼
               [Parallel Search]
                       │
     ┌─────────┬───────┼───────┬─────────┬─────────┬─────────┐
     ▼         ▼       ▼       ▼         ▼         ▼         ▼
  [Semantic][Matrix][Geometry][Graph][Template][Frequency][Recurrence]
     └─────────┴───────┼───────┴─────────┴─────────┴─────────┘
                       │
                       ▼
            [Reciprocal Rank Fusion] (RRF)
                       │
                       ▼
               [Top-K Candidates]
                       │
                       ▼
                [Context Builder] (Budget-Optimized Context)
                       │
                       ▼
               [Agent Connector] (LLM Response)
                       │
                       ▼
              [Verification Engine] (Confidence Check)
                       │
                       ▼
          [Final Answer with Citations]
```

---

## 5. Communication Protocols

| Layer | Protocol | Format |
| :--- | :--- | :--- |
| External API | HTTPS / REST | JSON |
| Internal services | gRPC + Protobuf | Binary |
| Database | PostgreSQL wire | SQL |
| Vector search | Qdrant REST / gRPC | JSON / Protobuf |
| Graph | Bolt / Cypher | Protobuf |
| Message queue | Redis Streams | Binary |
| Caching | Redis | Binary |
| Frontend | HTTPS / REST / WebSocket | JSON |
| Metrics | Prometheus exposition | Text |
| Logs | Fluentd → Elasticsearch | JSON |
| Tracing | OTLP | Protobuf |

---

## 6. Infrastructure Design

```
AWS Region: us-east-1
├── VPC (10.0.0.0/16)
│   ├── Public subnets × 3 AZs
│   └── Private subnets × 3 AZs
├── EKS Cluster (Kubernetes 1.28)
│   ├── Backend pods × 3-20 (HPA)
│   ├── Worker pods × 2-10 (HPA)
│   ├── Frontend pods × 2-4
│   └── Monitoring stack
├── RDS PostgreSQL (Multi-AZ, encrypted)
├── ElastiCache Redis (cluster mode)
├── S3 (versioned, encrypted backups)
├── Route53 + ACM (DNS + TLS)
└── Application Load Balancer
```

---

## 7. Scalability Model

### Horizontal scaling

- **API pods**: HPA 3-20 (CPU + Memory)
- **Worker pods**: HPA 2-10 (CPU)
- **Frontend pods**: HPA 2-4 (CPU)

### Vertical scaling

- Per-pod limits: 2 CPU, 4 GB memory (backend/worker)
- RDS: db.r6g.large → db.r6g.4xlarge
- Redis: cache.r6g.large → cache.r6g.4xlarge

### Data scaling

- Qdrant: scales to billions of vectors
- Neo4j: scales to billions of graph nodes
- PostgreSQL: scales via partitioning + read replicas

---

## 8. Security Model

- **Network**: TLS 1.3 at ingress, mTLS internal
- **Authentication**: JWT (HS256) + API keys + TOTP MFA
- **Authorization**: RBAC + ABAC
- **Encryption**: AES-256-GCM at rest, TLS in transit
- **Audit**: Hash-chained tamper-evident logs
- **Secrets**: Encrypted Vault, rotated regularly
- **Network policies**: default-deny + explicit allow
- **Container security**: non-root, read-only FS, dropped caps