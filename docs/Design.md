# AMDI-OS Design

## 1. Design Philosophy

### 1.1 Core Principles

1. **Separation of Concerns**: Each engine does ONE thing well.

2. **Composability**: All components are independently composable.

3. **Mathematical Rigor**: Every transformation has a formal basis.

4. **Production First**: Designed for deployment, not demos.

5. **Observable**: Every operation is measurable.

6. **Defensive**: Validate inputs, fail safely, audit everything.

### 1.2 Design Heuristics

- **Engine Independence**: Engines don't depend on each other; they operate on a common document representation.
- **Confidence Propagation**: Every signal carries uncertainty.
- **Reversibility**: Where possible, transformations are invertible.
- **Bounded Resources**: All operations have explicit memory/time budgets.
- **Graceful Degradation**: Partial failures don't cascade.

## 2. Design Patterns

### 2.1 Creational Patterns

| Pattern | Usage |
|---------|-------|
| **Factory** | `ConnectorFactory` creates AI agent connectors by name |
| **Builder** | `TensorBuilder`, `ContextBuilder` for complex object construction |
| **Singleton** | `MemoryEngine`, `ExportEngine` (one per process) |

### 2.2 Structural Patterns

| Pattern | Usage |
|---------|-------|
| **Facade** | `OptimizationEngine`, `SecurityEngine` simplify complex subsystems |
| **Composite** | Engine hierarchies (12 engines unified via common interface) |
| **Adapter** | Connector adapters for different AI agent APIs |
| **Bridge** | Separates memory storage from interface |

### 2.3 Behavioral Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | `TokenStrategy`, `MemoryStrategy`, `LatencyStrategy` swappable algorithms |
| **Observer** | Audit logger observes all engine events |
| **Chain of Responsibility** | `RetrievalEngine` chains 7 search methods |
| **Command** | `OptimizationEngine` queues optimization commands |
| **State** | `ConnectionStatus` (DISCONNECTED → CONNECTED → ERROR) |

### 2.4 Concurrency Patterns

| Pattern | Usage |
|---------|-------|
| **Producer-Consumer** | Celery workers process document queues |
| **Thread Pool** | `LatencyOptimizer.parallelize` |
| **Promise/Future** | Async AI agent calls |

## 3. Engineering Standards

### 3.1 Code Style

- **PEP 8** for Python
- **Black** formatter (line length 100)
- **Ruff** for linting
- **mypy** strict type checking
- **isort** for import ordering

### 3.2 Type Safety

```python

from typing import Dict, List, Optional, Tuple

from numpy.typing import NDArray

def process(

    data: NDArray[np.float64],

    config: Dict[str, Any],

    threshold: Optional[float] = None,

) -> Tuple[List[int], float]:

    ...

### 3.3 Error Handling

class CustomException(Exception):

    """Base for module-specific errors."""

try:

    result = risky_operation()

except SpecificError as exc:

    logger.error(f"Operation failed: {exc}", exc_info=True)

    raise

### 3.4 Logging

Structured JSON logging

Request/User ID via MDC

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Log rotation: 100 MB × 30 days

## 4. Object Models

### 4.1 Document Object Model

Document

```
├── ID, metadata
├── Pages[]
│   ├── Number, layout
│   ├── Elements[]
│   │   ├── Type (text/table/image)
│   │   ├── Bounding box (geometry)
│   │   └── Content
│   └── Tables[]
└── Language, encoding
```

### 4.2 Engine Output Model

EngineOutput

```
├── engine_name: str
├── data: Dict[str, Any]
├── confidence: float [0, 1]
├── latency_ms: float
├── metadata: Dict
└── timestamp: str
```

### 4.3 Universal Export Object

UniversalExportObject

```
├── system: str
├── context: str
├── summary: str
├── citations: List[Citation]
├── metadata: Dict
├── tables, images, graphs
├── confidence: float
├── total_tokens: int
└── version: str
```

## 5. UML Diagrams

### 5.1 Component Diagram

```
┌──────────────────┐
│  DocumentLoader  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Document       │◄──── 12 Engines (read)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐    ┌────────────────┐
│  EngineOutput[]  │───►│ Fusion Engine  │
└──────────────────┘    └────────┬───────┘
                                 │
                                 ▼
                       ┌────────────────┐
                       │ Fused Scores   │
                       └────────┬───────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  Memory   │   │ Retrieval │   │  Context  │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │               │               │
              └───────────────┴───────────────┘
                              │
                              ▼
                  ┌──────────────────────┐
                  │   UniversalExport   │
                  │      Object          │
                  └──────────┬───────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ AI Agent       │
                    │  Connector     │
                    └────────────────┘
```

### 5.2 Sequence Diagram: Document Query

User → Frontend → API → RetrievalEngine

```
                              │
                              ├──► SemanticSearch.search()
                              ├──► MatrixSearch.search()
                              ├──► GraphSearch.pagerank()
                              ├──► TemplateSearch.search()
                              ├──► FrequencySearch.search()
                              ├──► RecurrenceSearch.query()
                              │
                              ▼
```

                       HybridRanker.fuse(RRF)

```
                              │
                              ▼
```

                       ContextBuilder.build()

```
                              │
                              ▼
```

                       ExportEngine.build_ueo()

```
                              │
                              ▼
```

                       Connector.send_ueo()

```
                              │
                              ▼
```

                       VerificationEngine.verify()

```
                              │
                              ▼
```

                          Response → User

## 6. Component Design

### 6.1 Engine Component

class BaseEngine(ABC):

    """All engines implement this interface."""

    @abstractmethod

    def process(self, document: Document) -> EngineOutput:

        ...

    @abstractmethod

    def get_metrics(self) -> EngineMetrics:

        ...

### 6.2 Memory Component

HierarchicalMemory

```
├── L0_Raw (raw content, OCR text)
├── L1_Templates (fingerprints)
├── L2_Structures (graphs, topologies)
├── L3_Tables (matrix representations)
├── L4_Semantic (embeddings)
└── L5_Summaries (compressed summaries)
```

### 6.3 Retrieval Component

HybridRetriever

```
├── SemanticSearch (cosine, dot, euclidean)
├── MatrixSearch (column/row/SVD)
├── GeometrySearch (k-NN, radius, bbox)
├── GraphSearch (PageRank, BFS)
├── TemplateSearch (hamming, jaccard)
├── FrequencySearch (TF-IDF, BM25)
├── RecurrenceSearch (LSH, MinHash)
└── HybridRanker (RRF, Borda, Condorcet)
```

## 7. Dependency Graphs

Documents → Engines → Fusion → Memory → Retrieval → Context → Export → Connectors → Verification

(Independent)   (Reads)   (Writes)  (Stores)   (Queries)  (Builds) (Format) (Sends)    (Validates)

Reverse dependency

Verification ← Connectors ← Export ← Context ← Retrieval ← Memory ← Fusion ← Engines ← Documents

No circular dependencies.

## 8. Interface Design

### 8.1 REST API Endpoints

POST   /api/v1/documents              Upload document

GET    /api/v1/documents/{id}         Get document

POST   /api/v1/documents/{id}/process Run engines

POST   /api/v1/search                  Hybrid retrieval

POST   /api/v1/context                 Build context

POST   /api/v1/agents/{name}/send     Send to AI agent

POST   /api/v1/verify                  Verify response

GET    /api/v1/dashboards/*           Dashboard data

GET    /api/v1/health                  Health check

GET    /api/v1/metrics                 Prometheus metrics

### 8.2 gRPC Services (Internal)

engine.proto       — ProcessDocument(Document) → EngineOutputs

fusion.proto       — Fuse(EngineOutputs) → FusedScore

memory.proto       — Store/Retrieve/Promote/Evict

retrieval.proto    — Search(Query) → RetrievalResult

export.proto       — Export(Context) → UEO

verification.proto — Verify(UEO, Response) → VerificationResult

## 9. Error Handling Design

Error Hierarchy

AMDIError

```
├── IngestionError
│   ├── UnsupportedFormatError
│   ├── OCRError
│   └── CorruptedFileError
├── EngineError
│   ├── InvalidInputError
│   └── ProcessingTimeoutError
├── FusionError
├── MemoryError
│   └── CapacityExceededError
├── RetrievalError
│   ├── EmptyIndexError
│   └── InvalidQueryError
├── ContextError
│   └── TokenBudgetExceededError
├── ExportError
├── ConnectorError
│   ├── AuthenticationError
│   ├── RateLimitError
│   └── TimeoutError
├── VerificationError
│   ├── CitationMissingError
│   └── HallucinationDetectedError
├── SecurityError
│   ├── AuthorizationError
│   └── EncryptionError
└── DeploymentError
```

Recovery Strategies

Retry with exponential backoff (transient errors)

Circuit breaker (cascading failures)

Fallback to simpler algorithm (degradation)

Dead letter queue (permanent failures)

Graceful error messages (UX-friendly)

---