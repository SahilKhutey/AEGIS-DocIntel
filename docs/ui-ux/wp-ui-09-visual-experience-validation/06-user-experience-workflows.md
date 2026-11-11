# WP-UI-09 — 06: User Experience Workflows & End-to-End Journeys

**Work Package**: WP-UI-09 — Visual, Interaction & End-to-End Experience Validation  
**Document**: 06 — Critical User Journey Specifications & Execution Logs  
**Status**: Approved & Baseline Verified  
**Execution File**: `web/tests/e2e/` (65 automated workflow tests passing)  

---

## 1. Overview & Workflow Architecture

The ultimate test of the AEGIS-DocIntel workbench is the seamless execution of complete, multi-step user workflows. A feature is complete only when its entire lifecycle—from trigger to persistence, asynchronous backend synchronization, error recovery, and human verification—has been empirically validated.

The suite automates six core enterprise workflows covering all primary user personas:
1. **WF-DOC**: Document Ingestion, Lifecycle, and Inspection Workflow.
2. **WF-ASK**: Grounded Intelligence Querying, Citation Verification, and Feedback.
3. **WF-CMP**: Cross-Document Comparison, Semantic Alignment, and Diff Analysis.
4. **WF-GOV**: Human Review Queue, Claim Verification, Rationale Submission, and Audit.
5. **WF-OPS**: Pipeline DAG Telemetry, Execution Monitoring, and Diagnostics.
6. **WF-AUTH**: Sovereign Authentication, Session Renewal, and Tenant Switching.

---

## 2. Workflow Specification Matrix

### 2.1 WF-DOC: Document Ingestion & Lifecycle (11 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-DOC-001** | Open upload modal via "Upload Documents" primary CTA | `/documents` | **PASS** |
| **WF-DOC-002** | File selection via native file input or drag-and-drop | `/documents` | **PASS** |
| **WF-DOC-003** | Immediate client-side validation of file extension & size | `/documents` | **PASS** |
| **WF-DOC-004** | Upload progress bar rendering with byte percentage | `/documents` | **PASS** |
| **WF-DOC-005** | Backend ingestion job submission (`POST /api/v1/documents`) | `/documents` | **PASS** |
| **WF-DOC-006** | Real-time status badge update (`PENDING` -> `PROCESSING` -> `READY`)| `/documents` | **PASS** |
| **WF-DOC-007** | Search and filter library by document filename and status | `/documents` | **PASS** |
| **WF-DOC-008** | Click document row to navigate to inspector (`/documents/[id]`) | `/documents/[id]`| **PASS** |
| **WF-DOC-009** | Inspect document metadata, page rendering, and extracted text | `/documents/[id]`| **PASS** |
| **WF-DOC-010** | Delete document with confirmation dialog | `/documents` | **PASS** |
| **WF-DOC-011** | Error handling for corrupted or unsupported file types | `/documents` | **PASS** |

### 2.2 WF-ASK: Grounded Intelligence Q&A (11 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-ASK-001** | Compose question in QuestionComposer input textarea | `/ask` | **PASS** |
| **WF-ASK-002** | Submit question via click or `Cmd+Enter` keyboard shortcut | `/ask` | **PASS** |
| **WF-ASK-003** | Display loading skeleton and query progress indicators | `/ask` | **PASS** |
| **WF-ASK-004** | Stream natural language response with grounded citations | `/ask` | **PASS** |
| **WF-ASK-005** | Click citation badge `[1]` to open source evidence drawer | `/ask` | **PASS** |
| **WF-ASK-006** | Verify verbatim source text span highlighted in drawer | `/ask` | **PASS** |
| **WF-ASK-007** | Display document title, page number, and bounding box coordinates | `/ask` | **PASS** |
| **WF-ASK-008** | Submit user feedback (Thumbs Up / Down) with optional comments | `/ask` | **PASS** |
| **WF-ASK-009** | Copy grounded answer to clipboard with formatted markdown citations | `/ask` | **PASS** |
| **WF-ASK-010** | Query history sidebar navigation and query replay | `/ask` | **PASS** |
| **WF-ASK-011** | Empty query and out-of-domain query graceful error handling | `/ask` | **PASS** |

### 2.3 WF-CMP: Document Comparison & Diffing (8 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-CMP-001** | Select baseline document from dropdown picker | `/compare` | **PASS** |
| **WF-CMP-002** | Select target document for comparison | `/compare` | **PASS** |
| **WF-CMP-003** | Trigger comparison analysis (`POST /api/v1/compare`) | `/compare` | **PASS** |
| **WF-CMP-004** | Render side-by-side split comparison view | `/compare` | **PASS** |
| **WF-CMP-005** | Display visual diff highlights (additions in green, removals in red) | `/compare` | **PASS** |
| **WF-CMP-006** | Semantic clause alignment table and similarity scores | `/compare` | **PASS** |
| **WF-CMP-007** | Filter comparison differences by severity / significance | `/compare` | **PASS** |
| **WF-CMP-008** | Export comparison summary as PDF / Markdown report | `/compare` | **PASS** |

### 2.4 WF-GOV: Human Review & Decision Governance (15 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-GOV-001** | Load pending human review queue with priority badges | `/reviews` | **PASS** |
| **WF-GOV-002** | Filter review items by status (`PENDING`, `APPROVED`, `REJECTED`) | `/reviews` | **PASS** |
| **WF-GOV-003** | Select review claim item to inspect supporting evidence | `/reviews` | **PASS** |
| **WF-GOV-004** | FactVerificationPanel displays extracted fact vs verbatim source | `/reviews` | **PASS** |
| **WF-GOV-005** | Select verification verdict (`VERIFIED`, `CONTRADICTED`, `UNVERIFIABLE`)| `/reviews` | **PASS** |
| **WF-GOV-006** | Require mandatory reviewer rationale before submission | `/reviews` | **PASS** |
| **WF-GOV-007** | Submit review decision (`POST /api/v1/governance/decisions`) | `/reviews` | **PASS** |
| **WF-GOV-008** | ConflictResolutionPanel handles conflicting multi-document claims | `/reviews` | **PASS** |
| **WF-GOV-009** | Resolve conflict by choosing authoritative source and rationale | `/reviews` | **PASS** |
| **WF-GOV-010** | Immutable AuditTimeline reflects newly recorded human decision | `/reviews` | **PASS** |
| **WF-GOV-011** | Cryptographic hash and timestamp rendered in audit entry | `/reviews` | **PASS** |
| **WF-GOV-012** | Filter audit timeline by reviewer identity or date range | `/reviews` | **PASS** |
| **WF-GOV-013** | Require confirmation checkbox before executing irreversible rejection | `/reviews` | **PASS** |
| **WF-GOV-014** | Optimistic update removes reviewed item from pending queue | `/reviews` | **PASS** |
| **WF-GOV-015** | Role check: non-reviewers cannot approve or reject items | `/reviews` | **PASS** |

### 2.5 WF-OPS: Operational Telemetry & Pipelines (10 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-OPS-001** | Render pipeline DAG execution stages (`OCR`, `EXTRACT`, `INDEX`) | `/pipelines` | **PASS** |
| **WF-OPS-002** | Click pipeline stage node to inspect stage execution details | `/pipelines` | **PASS** |
| **WF-OPS-003** | Display stage execution latency, memory usage, and status | `/pipelines` | **PASS** |
| **WF-OPS-004** | Stage failure highlighted in red with drill-down error logs | `/pipelines` | **PASS** |
| **WF-OPS-005** | Service health status list displays all microservices green | `/monitoring` | **PASS** |
| **WF-OPS-006** | Latency percentiles gauge (p50, p95, p99) reflects live telemetry | `/monitoring` | **PASS** |
| **WF-OPS-007** | Throughput chart renders requests-per-second timeseries | `/monitoring` | **PASS** |
| **WF-OPS-008** | System alerts list displays active warnings and resolved alerts | `/monitoring` | **PASS** |
| **WF-OPS-009** | TimeRangeSelector toggles telemetry window (`1h`, `24h`, `7d`, `30d`) | `/monitoring` | **PASS** |
| **WF-OPS-010** | Developer portal key creation and credential revocation | `/developer` | **PASS** |

### 2.6 WF-AUTH: Authentication & Isolation (10 Tests)
| Test ID | Workflow Step / Verification Assertion | Target Route | Status |
| :--- | :--- | :--- | :---: |
| **WF-AUTH-001** | Sovereign JWT token storage in secure cookie / memory | Global | **PASS** |
| **WF-AUTH-002** | Development bypass mode for local offline engineering | Global | **PASS** |
| **WF-AUTH-003** | Session expiration detection and graceful re-authentication prompt | Global | **PASS** |
| **WF-AUTH-004** | Switch active tenant workspace in application shell header | Global | **PASS** |
| **WF-AUTH-005** | All subsequent API requests carry updated `X-Workspace-ID` | Global | **PASS** |
| **WF-AUTH-006** | In-memory caches cleared upon workspace context change | Global | **PASS** |
| **WF-AUTH-007** | RBAC permission gates render appropriate buttons/routes | Global | **PASS** |
| **WF-AUTH-008** | User profile popover displays active user, role, and organization | Global | **PASS** |
| **WF-AUTH-009** | Logout action invalidates tokens and cleans sensitive local state | Global | **PASS** |
| **WF-AUTH-010** | Cross-tenant data leakage prevention confirmed | Global | **PASS** |
