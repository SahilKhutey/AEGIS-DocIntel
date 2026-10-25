# AEGIS-DocIntel — Subsystem Specifications
**Version 1.0.0**

---

## S1. Ingestion Subsystem

### Purpose
Accepts raw documents from clients, validates them, stores them in object storage,
and dispatches ingestion jobs to the processing pipeline.

### Components
| Component          | Technology               | Scale                      |
|--------------------|--------------------------|----------------------------|
| REST API           | FastAPI + uvicorn        | 4 replicas, HPA CPU > 70%  |
| gRPC endpoint      | gRPC + protobuf          | Same pool as REST          |
| Auth middleware    | JWT (RS256) + API keys   | Stateless                  |
| Rate limiter       | Redis token bucket       | Per-tenant configurable     |
| Virus scanner      | ClamAV (async)           | Sidecar container          |
| Object storage     | MinIO / AWS S3           | Multi-AZ, versioned        |
| Job queue          | Apache Kafka             | 16 partitions              |

### API Endpoints
```
POST   /v1/documents/upload        Upload PDF
GET    /v1/documents/{doc_id}      Get document status
DELETE /v1/documents/{doc_id}      Delete document + all chunks
GET    /v1/documents               List documents (paginated)
POST   /v1/documents/batch         Batch upload manifest
GET    /v1/documents/{doc_id}/chunks  List chunks
```

### Kafka Topics
| Topic         | Partitions | Retention | Purpose                     |
|---------------|------------|-----------|-----------------------------|
| doc.ingest    | 16         | 7 days    | New ingestion jobs          |
| doc.indexed   | 16         | 7 days    | Indexing completion events  |
| doc.failed    | 4          | 30 days   | Failed jobs (DLQ)           |
| doc.reindex   | 8          | 7 days    | Re-indexing triggers        |

---

## S2. Document Engine Subsystem

### Purpose
Parses raw PDFs into structured, typed content blocks (text, tables, figures,
equations) with bounding boxes, page references, and extracted metadata.

### Sub-components
| Sub-component       | Technology                      |
|---------------------|---------------------------------|
| PDF Parser          | PyMuPDF (fitz) primary          |
| Table Parser        | pdfplumber + Camelot + TATR     |
| Layout Classifier   | DiT (Microsoft) + LayoutLMv3   |
| OCR Engine          | PaddleOCR → Tesseract → DocTR  |
| Equation OCR        | Nougat + Pix2Text               |
| Figure Captioner    | BLIP-2 / LLaVA                 |
| Chart Extractor     | ChartQA + Deplot               |

### Block Types
| Type      | Description                        | Storage           |
|-----------|------------------------------------|-------------------|
| text      | Paragraph, sentence, span          | Postgres + Milvus |
| header    | Section heading (H1-H6)            | Postgres + Milvus |
| footer    | Page footer                        | Postgres only     |
| table     | Structured grid → Markdown         | Postgres + Milvus |
| figure    | Cropped image + caption            | S3 + Milvus       |
| equation  | LaTeX string + rendered PNG        | S3 + Milvus       |
| caption   | Figure/table caption text          | Postgres + Milvus |
| footnote  | Footnote content                   | Postgres only     |

---

## S3. Chunking Subsystem

### Purpose
Divides parsed blocks into optimally-sized chunks for embedding and retrieval,
preserving semantic coherence and respecting token limits.

### Strategies

#### Hierarchical Chunking (default for structured docs)
```
Document
  └── Chapter / Section (by heading)
        └── Paragraph (by line break + similarity)
              └── Sentence (fallback for long paragraphs)
```

#### Semantic Chunking (for unstructured docs)
- Compute embedding for each sentence
- Split where cosine distance drops below threshold (0.35)
- Ensures each chunk is semantically self-contained

#### Sliding Window (fallback for uniform text)
- Window: 800 tokens
- Overlap: 100 tokens
- Ensures no information is split at chunk boundary

### Token Budget Rules
| Rule                     | Value          |
|--------------------------|----------------|
| Max tokens per chunk     | 800            |
| Min tokens per chunk     | 50             |
| Overlap between chunks   | 100 tokens     |
| Table: split threshold   | 1200 tokens    |
| Equation: never split    | atomic unit    |

---

## S4. Embedding Subsystem

### Purpose
Converts text chunks and visual content into dense vector representations
for semantic similarity search.

### Models

#### Text Embeddings
| Model                    | Dimension | Max Tokens | Use Case              |
|--------------------------|-----------|------------|-----------------------|
| BGE-large-en-v1.5        | 1024      | 512        | Primary (quality)     |
| jina-embeddings-v2-base  | 768       | 8192       | Long chunks           |
| text-embedding-3-large   | 3072      | 8191       | OpenAI (managed)      |

#### Visual Embeddings
| Model                | Dimension | Use Case                          |
|----------------------|-----------|-----------------------------------|
| ColPali              | 128×128   | Page-level late interaction       |
| ColQwen2             | 128×128   | Enhanced page understanding       |
| CLIP ViT-L/14        | 768       | Figure/chart embeddings           |

### Processing Pipeline
```python
# Batch embedding with GPU acceleration
chunks → tokenize (BGE tokenizer)
       → model forward pass (GPU, batch=32)
       → L2 normalize
       → return np.ndarray(n, 1024)
```

### Infrastructure
- GPU pool: A100 (80GB) or H100 (80GB)
- Autoscaling: KEDA on queue depth
- Throughput: ~5M tokens/min per GPU
- Fallback: CPU embedding (slower, no GPU dependency)

---

## S5. Vector Store Subsystem

### Purpose
Stores and indexes dense vector embeddings for approximate nearest neighbor (ANN)
search at 100M+ document scale.

### Milvus Cluster Architecture
```
Client
  └── Milvus Proxy (load balanced)
        ├── Query Node 1  ─── S3 (segment data)
        ├── Query Node 2  ─── MinIO
        ├── Query Node 3  ─── etcd (metadata)
        ├── Index Node 1  ─── Build HNSW index
        ├── Index Node 2
        ├── Data Node 1   ─── Receive inserts
        └── Data Node 2
```

### Collections

#### chunks_text
| Field       | Type           | Index                |
|-------------|----------------|----------------------|
| chunk_id    | VARCHAR (PK)   | -                    |
| doc_id      | VARCHAR        | Inverted (filter)    |
| tenant_id   | VARCHAR        | Inverted (filter)    |
| embedding   | FLOAT_VECTOR(1024) | HNSW              |
| page        | INT64          | -                    |
| block_type  | VARCHAR        | Inverted (filter)    |
| token_count | INT64          | -                    |
| text        | VARCHAR        | -                    |
| section     | VARCHAR        | -                    |

#### chunks_visual
| Field         | Type               | Index             |
|---------------|--------------------|-------------------|
| chunk_id      | VARCHAR (PK)       | -                 |
| doc_id        | VARCHAR            | Inverted (filter) |
| tenant_id     | VARCHAR            | Inverted (filter) |
| page          | INT64              | -                 |
| visual_embed  | FLOAT_VECTOR(1024) | HNSW              |
| image_s3      | VARCHAR            | -                 |

### HNSW Index Parameters
| Parameter      | Value  | Rationale                      |
|----------------|--------|--------------------------------|
| M              | 16     | Memory vs accuracy balance     |
| efConstruction | 200    | Build quality (offline)        |
| ef (search)    | 128    | Search quality (online)        |
| metric_type    | COSINE | Normalized embeddings          |

### Capacity Planning (100M docs)
| Metric           | Calculation                | Total     |
|------------------|----------------------------|-----------|
| Chunks per doc   | ~30 avg                    | 3B chunks |
| Vector size      | 1024 × 4 bytes             | 4 KB/vec  |
| Raw vectors      | 3B × 4 KB                  | 12 TB     |
| HNSW overhead    | ~20× raw                   | ~240 TB   |
| Query nodes      | 240 TB / 2 TB RAM each     | 120 nodes |
| With replication | × 2                        | 240 nodes |

---

## S6. Search & Retrieval Subsystem

### Purpose
Implements hybrid BM25 + dense + visual retrieval with reciprocal rank fusion
and cross-encoder reranking for maximal recall and precision.

### Elasticsearch Configuration (BM25)
```json
{
  "settings": {
    "number_of_shards": 32,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "aegis_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball", "word_delimiter_graph"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "chunk_id":   { "type": "keyword" },
      "doc_id":     { "type": "keyword" },
      "tenant_id":  { "type": "keyword" },
      "text":       { "type": "text", "analyzer": "aegis_analyzer",
                      "similarity": "BM25" },
      "block_type": { "type": "keyword" },
      "page":       { "type": "integer" },
      "section":    { "type": "text" }
    }
  }
}
```

### BM25 Parameters
| Parameter | Value | Effect                           |
|-----------|-------|----------------------------------|
| k1        | 1.5   | Term frequency saturation        |
| b         | 0.75  | Document length normalization    |

### Reciprocal Rank Fusion (RRF)
```
score(d) = Σ 1/(k + rank_i(d))   for each ranking i
k = 60  (standard RRF parameter)
```

### Cross-Encoder Reranking
- Model: BAAI/bge-reranker-v2-m3 (multilingual)
- Input: (query, chunk) pairs (top 80 from RRF)
- Output: relevance score ∈ [0, 1]
- Threshold: score < 0.2 → excluded
- Top K: dynamic (8–20 based on token budget)

### Query Transformation
| Method      | Description                                      | Benefit              |
|-------------|--------------------------------------------------|----------------------|
| HyDE        | Generate hypothetical answer, embed it           | +8% Recall           |
| Step-back   | Abstract to concept level                        | +5% MRR              |
| Multi-query | 3 paraphrases → union → rerank                  | +12% Recall          |
| Decompose   | Split complex → sub-questions → join answers    | +15% on multi-hop    |

---

## S7. Context Builder Subsystem

### Purpose
Assembles the final LLM prompt from retrieved chunks, respecting strict token
budgets and optimizing for LLM comprehension.

### Token Budget Allocation
```
TOTAL BUDGET: 8,500 tokens (input)

├── System prompt + instructions:   1,200 tokens  (14%)
├── Tool definitions:                 300 tokens  (3.5%)
├── User question:                    200 tokens  (2.4%)
├── Conversation history:             800 tokens  (9.4%)
├── Citation scaffold:                400 tokens  (4.7%)
└── Retrieved chunks:               5,600 tokens  (65%)   ← maximize
                                  ─────────────
                                    8,500 tokens
```

### Chunk Ordering
1. Sort by document order (page number, then chunk_index)
2. Prepend section headers for context
3. Inject source tags: `[Source-1: {doc_name}, p.{page}]`

### Prompt Compression (LLMLingua-2)
- If chunks exceed budget: compress with LLMLingua-2
- Target compression ratio: 0.5x (50% token reduction)
- Preserves key facts, discards filler text

---

## S8. LLM Service Subsystem

### Purpose
Provides unified LLM inference with provider failover, streaming, tool use,
and cost tracking.

### Provider Hierarchy
```
Primary:  vLLM (self-hosted) → Llama-3.3-70B / DeepSeek-V3
Fallback: OpenAI GPT-4o
Fallback: Anthropic Claude-3.5-Sonnet
Fallback: Google Gemini-1.5-Pro
Emergency: Qwen-2.5-7B (low-resource local)
```

### vLLM Configuration
```yaml
model: meta-llama/Llama-3.3-70B-Instruct
tensor_parallel_size: 4        # 4× A100 80GB
gpu_memory_utilization: 0.92
max_num_seqs: 256
max_model_len: 131072
enable_prefix_caching: true    # KV cache reuse
quantization: awq              # 4-bit, minimal quality loss
dtype: bfloat16
```

### Tool Definitions
| Tool         | Trigger                        | Implementation        |
|--------------|--------------------------------|-----------------------|
| calculator   | Math expressions in question   | Python eval sandbox   |
| code_exec    | "Run this code" / "Calculate"  | Isolated container    |
| web_search   | Confidence < 0.4 on retrieval  | Tavily / SerpAPI      |
| doc_lookup   | Cross-document reference       | Internal RAG call     |

---

## S9. Observability Subsystem

### Golden Signals (Grafana Dashboards)
| Signal      | Metric                                | Alert Threshold     |
|-------------|---------------------------------------|---------------------|
| Latency     | aegis_retrieval_latency_seconds p99   | > 1.5s              |
| Traffic     | aegis_queries_total (rate/5m)         | < 10% of baseline   |
| Errors      | aegis_errors_total (rate/5m)          | > 1%                |
| Saturation  | GPU utilization, Kafka lag            | GPU > 85%, lag >10K |

### Trace Spans
Every request generates traces:
```
query.receive → cache.lookup → retrieval.bm25 → retrieval.dense
→ retrieval.rerank → context.build → llm.inference → response.generate
```

### Log Format (structured JSON)
```json
{
  "timestamp": "2026-06-18T10:00:00Z",
  "level": "INFO",
  "service": "aegis-query",
  "trace_id": "abc123",
  "span_id": "def456",
  "tenant_id": "uuid",
  "doc_id": "uuid",
  "event": "retrieval_complete",
  "chunks_retrieved": 12,
  "latency_ms": 87
}
```

---

## S10. Security Subsystem

### Authentication
- JWT (RS256, 1h expiry) + refresh tokens (7d, rotating)
- API keys for service-to-service (SHA-256 HMAC)
- Optional: OIDC SSO (Keycloak / Auth0)

### Authorization
- RBAC: admin / editor / viewer per tenant
- Document-level ACL in Postgres (row-level security)
- Chunk-level: inherits parent document ACL

### Encryption
| Layer           | Algorithm               |
|-----------------|-------------------------|
| At rest (S3)    | AES-256-GCM             |
| At rest (DB)    | PostgreSQL TDE (pgcrypto) |
| In transit      | TLS 1.3 (min)           |
| Service mesh    | Istio mTLS              |

### Audit Trail
```sql
CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    tenant_id   UUID,
    user_id     UUID,
    action      TEXT,       -- upload|query|delete|export
    resource    TEXT,       -- doc_id or 'collection'
    ip_address  INET,
    user_agent  TEXT,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);
-- Partition by month, append-only, no DELETE permission
```
