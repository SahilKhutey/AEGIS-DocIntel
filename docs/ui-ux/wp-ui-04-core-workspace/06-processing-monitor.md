# 06 — Processing Monitor

## 1. Asynchronous Telemetry & Pipeline Monitoring

The Processing Monitor (`/processing`) provides comprehensive operational telemetry over asynchronous document processing jobs, background vector embedding tasks, and fact extraction routines. It maps to the FastAPI `/v1/jobs` router.

---

## 2. Interface Anatomy

```
+-----------------------------------------------------------------------------------------+
| Processing Monitor                                                                      |
| Real-time telemetry and pipeline execution tracking for document ingestion and indexing.|
|                                                                             [ Refresh ] |
+-----------------------------------------------------------------------------------------+
| Status: [ All ] [ Running ] [ Failed ] [ Succeeded ] [ Queued ]                         |
+-----------------------------------------------------------------------------------------+
| Document / Resource    | Job Type    | Status    | Progress | Attempt | Updated  | Action |
|------------------------+-------------+-----------+----------+---------+----------+--------|
| v security_policy.docx | INDEX DOC   | Running   | [==   ]  | 1 / 3   | 10:02 AM |        |
|   +-----------------------------------------------------------------------------------+ |
|   | Execution Pipeline Breakdown                                                      | |
|   | 1. (✓) File Ingestion & Validation (0.9s)                                         | |
|   | 2. (✓) Text Extraction & OCR (1.1s)                                               | |
|   | 3. (⟳) Chunking & Layout Analysis [Active Stage]                                  | |
|   | 4. ( ) Embedding & Vector Indexing                                                | |
|   | 5. ( ) Structured Fact Extraction                                                 | |
|   | 6. ( ) Knowledge Synthesis                                                        | |
|   +-----------------------------------------------------------------------------------+ |
| > vendor_contract.pdf  | INDEX DOC   | Failed    | [=    ]  | 3 / 3   | 10:05 AM | [Retry]|
| > acme_q3_report.pdf   | EXTRACT FACT| Succeeded | [====]   | 1 / 3   | 10:05 AM |        |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Pipeline Stage Execution Timeline (`ProcessingTimeline`)

The pipeline breakdown uses semantic ordered lists:
```html
<ol aria-label="Processing stages" class="relative border-l ...">
  <li class="ml-6" aria-current="step">
    <!-- Active running stage with pulsing indicator -->
  </li>
  <li class="ml-6">
    <!-- Completed stage with checkmark -->
  </li>
</ol>
```

### Stages in the Standard Pipeline:
1. **File Ingestion & Validation**: Checksum calculation, format verification, and virus/malware inspection.
2. **Text Extraction & OCR**: Optical character recognition and layout-aware stream extraction.
3. **Chunking & Layout Analysis**: Table boundary detection, heading hierarchy parsing, and semantic passage chunking.
4. **Embedding & Vector Indexing**: Generating dense embeddings and indexing into vector storage.
5. **Structured Fact Extraction**: LLM-guided entity-attribute triple extraction.
6. **Knowledge Synthesis**: Verification of citations and cross-document graph linking.

---

## 4. Failure Recovery & Polling

- **One-Click Retry**: For jobs in `failed` status, a `Retry` action button issues a `POST` request to `/api/v1/jobs/{job_id}/retry`. Upon confirmation, the job transitions back to `queued` / `running` status and the monitor refreshes.
- **Smart Polling**: When active jobs (`running` or `queued`) are present, the page automatically polls `/api/v1/jobs` at configured intervals (default: 8,000ms). When all jobs reach terminal states (`succeeded`, `failed`, or `cancelled`), polling pauses to conserve server resources.
- **Accessible State Badges**:
  - `Succeeded`: `<Badge variant="success">` with `CheckCircle2` icon.
  - `Running`: `<Badge variant="info">` with animated `RotateCw` spinner.
  - `Failed`: `<Badge variant="danger">` with `AlertTriangle` warning icon.
  - `Retry Wait`: `<Badge variant="warning">` with clock icon.
  - `Queued`: `<Badge variant="default">` with clock icon.
