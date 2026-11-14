# WP-04.05 Dossier 02: Feature & Permission Catalogue

**Work Package:** PROT-04.05  
**Title:** Canonical Feature and Permission Catalogue Specification  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Overview & Separation of Concerns

To prevent scattering hardcoded strings and disparate authorization checks throughout the codebase, AEGIS-DocIntel separates **Capabilities (Features)** from **Operations (Permissions)**:
- **Feature (`<domain>.<capability>`)**: High-level functionality exposed to the evaluator or tier (e.g., `document.query`, `document.compare`).
- **Permission (`<resource>.<action>`)**: Fine-grained atomic operation required on a resource (e.g., `document.read`, `document.upload`, `workspace.update`).

Source Implementation: [`src/schemas/evaluation/entitlement_catalogue.py`](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/src/schemas/evaluation/entitlement_catalogue.py)

---

## 2. Canonical Feature Catalogue

### 2.1 Evaluation Features

| Feature Identifier | Description | Default Evaluation Policy (`evaluation-basic`) |
| :--- | :--- | :--- |
| `dashboard.view` | View personal evaluation dashboard | **Enabled** (`True`) |
| `document.upload` | Upload supported evaluation documents | **Enabled** (`True`, capped) |
| `document.preview` | View extracted text preview and OCR layout | **Enabled** (`True`) |
| `document.metadata` | Inspect document metadata and chunk stats | **Enabled** (`True`) |
| `document.parse` | Trigger document OCR and parsing pipeline | **Enabled** (`True`, capped) |
| `document.query` | Ask AEGIS grounded cross-document intelligence | **Enabled** (`True`, capped) |
| `document.compare` | Cross-document contradiction and delta analysis | **Disabled** (`False` in basic tier) |
| `document.export` | Export structured analysis results | **Disabled** (`False` in basic tier) |
| `workspace.manage` | Manage local evaluation workspace | **Enabled** (`True`, own scope only) |
| `usage.view` | Inspect quota consumption and rate limits | **Enabled** (`True`) |
| `license.view` | View active evaluation license details | **Enabled** (`True`) |
| `device.manage` | Deactivate bound evaluation device | **Enabled** (`True`) |

### 2.2 Administrative Features (Strictly Forbidden for Evaluators)

| Feature Identifier | Description | Policy Guard Rule |
| :--- | :--- | :--- |
| `admin.manage_users` | Create, modify, or delete evaluator accounts | **Strictly Denied** (`ENT-015`) |
| `admin.issue_license` | Mint cryptographic evaluation licenses | **Strictly Denied** (`ENT-015`) |
| `admin.revoke_license`| Revoke evaluation licenses | **Strictly Denied** (`ENT-015`) |
| `engine.admin` | Access private topology engine directly | **Strictly Denied** (`ENT-015`) |
| `internal.debug` | Internal telemetry and debug endpoints | **Strictly Denied** (`ENT-015`) |

---

## 3. Canonical Action-Level Permission Catalogue

Permissions follow the standard `<resource>.<action>` pattern:

| Permission Name | Resource Target | Associated Operation |
| :--- | :--- | :--- |
| `document.read` | Document | View preview, metadata, chunks, citations |
| `document.upload` | Document | Ingest and upload new files |
| `document.parse` | Document | Trigger OCR, table parsing, layout DAG |
| `document.query` | Intelligence | Run grounded Ask AEGIS queries |
| `document.compare` | Intelligence | Run pairwise topological comparison |
| `document.export` | Document | Export analysis reports or CSV/JSON results |
| `document.delete` | Document | Purge ingested document from session store |
| `workspace.read` | Workspace | Inspect evaluation workspace settings |
| `workspace.update` | Workspace | Update local workspace configurations |
| `usage.read` | Telemetry | Retrieve quota usage status |
| `license.read` | Licensing | Inspect license claims and expiration |
| `device.deactivate` | Device | Deactivate bound hardware device |

### Administrative Permission Namespace
- `admin.evaluation.issue`
- `admin.evaluation.suspend`
- `admin.evaluation.revoke`
- `admin.evaluation.inspect`
- `admin.users.manage`
- `admin.engine.manage`

---

## 4. Feature-to-Permission Mapping Matrix

```python
FEATURE_REQUIRED_PERMISSIONS = {
    "dashboard.view": {"usage.read", "license.read"},
    "document.upload": {"document.upload"},
    "document.preview": {"document.read"},
    "document.metadata": {"document.read"},
    "document.parse": {"document.parse", "document.read"},
    "document.query": {"document.query", "document.read"},
    "document.compare": {"document.compare", "document.read"},
    "document.export": {"document.export", "document.read"},
    "workspace.manage": {"workspace.read", "workspace.update"},
    "usage.view": {"usage.read"},
    "license.view": {"license.read"},
    "device.manage": {"device.deactivate"},
}
```

---

## 5. Backward Compatibility & Alias Normalization

To ensure existing test fixtures and older API client calls continue operating seamlessly without breaking changes:
- `document_upload` $\to$ `document.upload`
- `document_extraction` $\to$ `document.preview`
- `ask_aegis` $\to$ `document.query`
- `citation_inspection` $\to$ `document.preview`
- `document_comparison` $\to$ `document.compare`
- `documents.upload` $\to$ `document.upload`
- `documents.read` $\to$ `document.read`
- `intelligence.query` $\to$ `document.query`
