# AEGIS-DocIntel — End-to-End Workflow Specifications
**Version 1.0.0**

---

## Overview

This document defines all end-to-end workflows for the AEGIS-DocIntel platform,
from document upload through to structured response generation with citations.

---

## Workflow 1: Document Ingestion Pipeline

```
[Client] ──POST /v1/documents/upload (multipart, max 200MB)──►
         │
         ▼
[API Gateway]
  ├── JWT / API-key authentication
  ├── Tenant rate-limit check (Redis token bucket)
  ├── MIME-type validation (application/pdf, docx, pptx, html)
  ├── File-size validation
  └── Virus scan (ClamAV async)
         │
         ▼
[Ingestion Service]
  ├── Generate doc_id (UUID v7, time-ordered)
  ├── Store raw file → S3: s3://aegis-raw/{tenant_id}/{doc_id}/{filename}
  ├── Insert DB record: status=pending
  └── Publish to Kafka: topic=doc.ingest, key=tenant_id
         │
         ▼
[Kafka: doc.ingest] ─────────────────────────────────────────►
         │
         ▼
[Indexing Worker Pool] (Ray / Celery, autoscale on lag)
  │
  ├── Stage 1: PDF Parse
  │     ├── PyMuPDF: text + bboxes + metadata
  │     ├── pdfplumber: table extraction (lattice + stream)
  │     └── Detect scanned pages (text_chars < 50/page)
  │
  ├── Stage 2: Layout Analysis
  │     ├── DiT model: block type classification
  │     │     (text, table, figure, equation, header, footer)
  │     ├── LayoutLMv3 for complex multi-column layouts
  │     └── Reading order reconstruction
  │
  ├── Stage 3: OCR (scanned pages only)
  │     ├── Tier 1: PaddleOCR (accuracy + multilingual)
  │     ├── Tier 2: Tesseract 5 (fallback)
  │     ├── Tier 3: DocTR (document-specific)
  │     └── Tier 4: Surya OCR (state-of-the-art 2024+)
  │
  ├── Stage 4: Specialized Extraction
  │     ├── Tables → TableTransformer → Markdown
  │     ├── Equations → Nougat / Pix2Text → LaTeX
  │     ├── Figures → region crop → CLIP captioning
  │     ├── Charts → ChartQA → structured data
  │     └── Footnotes / References → linked metadata
  │
  ├── Stage 5: Semantic Chunking
  │     ├── Hierarchical: doc → section → paragraph → sentence
  │     ├── Semantic boundary detection (embedding cosine distance)
  │     ├── Token-limit enforcement: max 800 tokens / chunk
  │     ├── Overlap: 100 tokens between adjacent chunks
  │     └── Minimum: 50 tokens (merge tiny blocks)
  │
  ├── Stage 6: Text Embedding
  │     ├── Model: BGE-large-en-v1.5 (1024-d)
  │     ├── Long-text fallback: jina-embeddings-v2-base (8192 tok)
  │     ├── Batch size: 32 on GPU, 8 on CPU
  │     └── Normalization: L2 unit norm
  │
  ├── Stage 7: Visual Embedding (pages + figures)
  │     ├── Model: ColPali / ColQwen2
  │     ├── Page-level embeddings (late interaction)
  │     └── Figure-level embeddings (CLIP)
  │
  ├── Stage 8: Multi-Index Storage
  │     ├── Milvus: chunk_id + embedding + payload
  │     ├── Elasticsearch: chunk_id + bm25_text
  │     ├── Postgres: full chunk metadata + text
  │     ├── Redis: document processing state
  │     └── S3: page images, figure crops, derived JSON
  │
  └── Stage 9: Status Update
        ├── Postgres: status=ready, chunk_count, indexed_at
        ├── Kafka: topic=doc.indexed, key=doc_id
        └── WebSocket / callback to client
```

### Ingestion SLAs
| Stage             | P50    | P99    | Failure Action            |
|-------------------|--------|--------|---------------------------|
| Parse             | 0.5s   | 5s     | Retry x3 → DLQ           |
| Layout            | 1s     | 8s     | Skip → text-only mode     |
| OCR (per page)    | 2s     | 15s    | Retry x2 → mark degraded |
| Embedding (batch) | 0.2s   | 2s     | Retry x3 → DLQ           |
| Index write       | 0.1s   | 1s     | Retry x5 → DLQ           |

---

## Workflow 2: Query / RAG Pipeline

```
[Client] ──POST /v1/query { doc_ids?, question, top_k?, session_id }──►
         │
         ▼
[Query Service]
  │
  ├── Step 1: Authentication + ACL
  │     ├── Validate JWT / API key
  │     ├── Resolve tenant_id → allowed doc_ids
  │     └── Enforce row-level security filters
  │
  ├── Step 2: Semantic Cache Lookup
  │     ├── Embed question → q_vec
  │     ├── Redis FAISS lookup: cosine(q_vec, cached_queries)
  │     ├── Threshold: cosine ≥ 0.95 → CACHE HIT → return response
  │     └── MISS → proceed to retrieval
  │
  ├── Step 3: Query Transformation
  │     ├── HyDE: generate hypothetical document, embed it
  │     ├── Step-back prompting: abstract to concept level
  │     └── Multi-query: 3 query paraphrases → union results
  │
  ├── Step 4: Hybrid Retrieval (parallel)
  │     ├── BM25 Search:
  │     │     ├── Elasticsearch query: exact + stem + phrase
  │     │     ├── Filters: tenant_id, doc_ids, block_type
  │     │     └── Top 50 candidates (BM25 score + metadata)
  │     │
  │     ├── Dense Search:
  │     │     ├── Milvus HNSW cosine search
  │     │     ├── Filters: tenant_id, doc_ids, language
  │     │     └── Top 50 candidates (cosine similarity)
  │     │
  │     └── Visual Search (if question references visuals):
  │           ├── ColPali page-level lookup
  │           └── Top 20 pages (late interaction score)
  │
  ├── Step 5: Reciprocal Rank Fusion (RRF)
  │     ├── k=60 (standard RRF parameter)
  │     ├── Merge BM25 + Dense + Visual rankings
  │     └── Top 80 fused candidates
  │
  ├── Step 6: Cross-Encoder Reranking
  │     ├── Model: BGE-reranker-v2-m3 / FlashRank
  │     ├── Input: (question, chunk_text) pairs
  │     ├── Top 8–20 final chunks (based on context budget)
  │     └── Confidence score extraction
  │
  ├── Step 7: Diversity Filter (MMR)
  │     ├── λ=0.7 (relevance-diversity balance)
  │     ├── Prevents redundant chunk selection
  │     └── Ensures page coverage diversity
  │
  ├── Step 8: Context Builder
  │     ├── Token budget: 8,500 total input
  │     ├── System prompt: 1,200 tokens
  │     ├── User question: 200 tokens
  │     ├── Conversation history: 800 tokens (compressed)
  │     ├── Retrieved chunks: pack into remaining budget
  │     └── Sort chunks by document order (not relevance)
  │
  ├── Step 9: Prompt Construction
  │     ├── System: role + citation instructions
  │     ├── Context: [Chunk-1][Chunk-2]...[Chunk-N]
  │     ├── History: [User][Assistant]...[User]
  │     └── Question: {user_question}
  │
  ├── Step 10: LLM Inference
  │     ├── Primary: vLLM (self-hosted)
  │     ├── Fallback: OpenAI / Anthropic / Google
  │     ├── Streaming: yes (Server-Sent Events)
  │     ├── Tool calls: calculator, code_exec, web_search
  │     └── Max output: 4096 tokens
  │
  ├── Step 11: Citation Extraction
  │     ├── Map [Source-N] markers → chunk_id
  │     ├── Resolve chunk_id → page, section, bbox
  │     └── Build structured citation list
  │
  ├── Step 12: Cache Write
  │     ├── Store (q_vec, response) → semantic cache
  │     ├── Store session turn → episodic memory
  │     └── Update token ledger → Postgres
  │
  └── Return: { answer, citations, confidence, session_id, tokens_used }
```

### Query SLAs
| Step              | P50    | P99    |
|-------------------|--------|--------|
| Cache lookup      | 5ms    | 20ms   |
| BM25 retrieval    | 20ms   | 100ms  |
| Dense retrieval   | 30ms   | 150ms  |
| Reranking         | 50ms   | 300ms  |
| LLM (TTFT)        | 200ms  | 800ms  |
| LLM (full resp.)  | 500ms  | 1500ms |
| Total (cache hit) | 10ms   | 30ms   |
| Total (cache miss)| 500ms  | 1500ms |

---

## Workflow 3: Memory Lifecycle

```
[New Session]
     │
     ▼
[Session Create]
  ├── Generate session_id (UUID v7)
  ├── Init episodic buffer (empty, max 10 turns)
  └── Associate doc_ids + tenant_id

[Per Turn]
  ├── Load episodic history from Redis
  ├── Compress if > 4K tokens (T5 summarizer)
  ├── Build context: compressed_history + current_question
  └── After response: append turn to episodic buffer

[Session End / TTL]
  ├── Persist compressed summary to Postgres
  └── Expire Redis keys (TTL = 1h sliding)
```

---

## Workflow 4: Document Re-indexing

```
[Trigger: re-upload same doc_id OR manual API call]
     │
     ▼
  ├── Set document status = re_indexing
  ├── Delete all chunks from Milvus (doc_id filter)
  ├── Delete all chunks from Elasticsearch
  ├── Delete chunk records from Postgres
  ├── Invalidate all Redis semantic cache entries for doc
  ├── Invalidate document parse cache
  └── Re-run full ingestion pipeline (Workflow 1)
```

---

## Workflow 5: Failure & Fallback Handling

```
Dense Retrieval Fails
  → Fallback: BM25-only retrieval

LLM Primary Timeout (> 30s)
  → Fallback: smaller model (Qwen-2.5-7B)
  → If still fails: cached similar response

Vector DB Unavailable
  → Fallback: in-memory FAISS replica (warm cache, 24h TTL)

Kafka Consumer Lag > 10K messages
  → Scale-up workers (KEDA)
  → Alert on-call via PagerDuty

OCR Quality < 0.5 Confidence
  → Escalate to GPT-4V / Claude Vision OCR
  → Flag chunk as low_confidence in metadata

Document Parse Failure
  → Move to DLQ (dead-letter queue)
  → Alert + manual review UI
  → Partial index if > 50% pages succeeded
```

---

## Workflow 6: Batch Ingestion (100M+ Scale)

```
[Batch Job Trigger]
  │
  ▼
[S3 Manifest Upload]
  ├── manifest.json: [{s3_uri, doc_id?, tenant_id, priority}]
  └── Max: 1M entries per manifest

[Ray / Spark Distributed Processing]
  ├── Partition by tenant_id (even distribution)
  ├── Priority queue: HIGH → NORMAL → LOW
  ├── Worker pool: autoscale 100–1000 workers
  └── Progress tracking: Redis counters + Kafka events

[Rate Limiting]
  ├── Per-tenant: max 1000 docs/minute
  ├── Global: 10,000 docs/minute
  └── Backpressure: Kafka consumer pause
```
