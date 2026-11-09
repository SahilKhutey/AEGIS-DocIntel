# 05 — Document Inspection

## 1. Inspection Architecture

The Document Inspection interface (`/documents/[documentId]`) provides deep analytical inspection of source material, extracted knowledge, and pipeline execution logs. It satisfies the strict sovereign evidence verification requirement: every fact, answer, or citation must be traceable back to original source pages.

---

## 2. Inspector Tabs & Navigation

The Document Inspector uses standard WAI-ARIA tab semantics (`role="tablist"`, `role="tab"`, and `role="tabpanel"`):

```
+-----------------------------------------------------------------------------------------+
| [<- Back] acme_q3_financial_report.pdf [Completed]           [Extract Facts] [Ask Doc ->]
| ID: doc-alpha-001 · application/pdf · 3.50 MB                                           |
+-----------------------------------------------------------------------------------------+
| [ Overview ] [ Preview ] [ Extracted Text & Chunks (42) ] [ Facts (12) ] [ Meta ] [ Sum ]|
+-----------------------------------------------------------------------------------------+
| Document Overview                                                                       |
| Core identity, indexing lifecycle, and provenance.                                      |
|                                                                                         |
| Status: Completed      Page Count: 14          Chunks: 42                               |
| Ingested: 04/11/2026   Updated: 04/11/2026     MIME: application/pdf                    |
|                                                                                         |
| Indexed Chunks & Passages                                                               |
| Chunk 1 (Page 1) - Financial Highlights                                                 |
| "Acme Corporation reported Q3 2026 revenue of $142.5 million..."                       |
+-----------------------------------------------------------------------------------------+
```

### 2.1 Tab Specifications

1. **Overview Tab**:
   - High-level document identity card: status, page count, chunk count, timestamps, and MIME format.
   - Initial highlights of indexed chunks (section titles and text) and extracted facts summary, allowing immediate verification without manual tab switching.
2. **Preview Tab**:
   - Visual document rendering for formats supporting safe browser preview (PDF, HTML).
   - Graceful fallback for non-renderable formats.
3. **Extracted Text & Chunks Tab**:
   - Passage-by-passage inspection of chunked content.
   - Displays page numbers, unique chunk IDs (`chunk_id`), and section titles.
   - Source for vector embedding and grounding citations.
4. **Extracted Facts Tab**:
   - Structured entity-attribute-value triples extracted from the document.
   - Columns: *Subject*, *Attribute*, *Value*, *Confidence*, and evidence citation.
   - Interactive trigger to run on-demand extraction (`POST /api/v1/documents/{doc_id}/extract-facts`).
5. **Metadata Tab**:
   - Provenance details: file hash, tenant ID, ingestion timestamp, index version, and processing duration.
6. **Processing Summary Tab**:
   - Pipeline stages executed, stage-by-stage completion indicators, and confidence score aggregates.

---

## 3. Knowledge Extraction & Downstream Querying

- **On-Demand Fact Extraction**: Analysts can trigger structured entity extraction at any time by clicking "Extract Structured Facts". The system issues a `POST` request to `/api/v1/documents/{doc_id}/extract-facts` and updates the facts table upon completion.
- **Direct Analytical Querying**: Clicking "Ask on this Document" navigates to `/ask?doc_id={doc_id}`, automatically scoping all evidence retrieval to the current document.
