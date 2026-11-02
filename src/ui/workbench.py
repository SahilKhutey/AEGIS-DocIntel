"""
src/ui/workbench.py
===================
AEGIS-DocIntel — Single-Page Document Intelligence Workbench.
Serves a self-contained, responsive SPA directly from FastAPI with zero external
build tools, zero Node dependencies, and zero cross-origin configuration issues.
"""

from __future__ import annotations


def get_workbench_html() -> str:
    """Return the complete, self-contained HTML/CSS/JS document intelligence workbench."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AEGIS-DocIntel — Document Intelligence Workbench</title>
  <style>
    :root {
      --bg: #0f172a;
      --bg-panel: #1e293b;
      --bg-card: #ffffff;
      --bg-subtle: #f8fafc;
      --border: #e2e8f0;
      --border-dark: #334155;
      --text: #0f172a;
      --text-muted: #64748b;
      --text-light: #f8fafc;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-light: #eff6ff;
      --success: #16a34a;
      --success-light: #f0fdf4;
      --warning: #d97706;
      --warning-light: #fffbeb;
      --danger: #dc2626;
      --danger-light: #fef2f2;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--font);
      background-color: var(--bg-subtle);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* Top Global Header */
    header.global-header {
      background: var(--bg);
      color: var(--text-light);
      padding: 0.75rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border-dark);
      flex-wrap: wrap;
      gap: 1rem;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-icon {
      background: linear-gradient(135deg, #38bdf8, #6366f1);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.1rem;
      color: white;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-badge {
      background: rgba(255,255,255,0.12);
      font-size: 0.7rem;
      padding: 2px 8px;
      border-radius: 9999px;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: #93c5fd;
    }

    .header-controls {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .health-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.8rem;
      padding: 4px 10px;
      border-radius: 9999px;
      background: rgba(22, 163, 74, 0.15);
      color: #4ade80;
      border: 1px solid rgba(74, 222, 128, 0.3);
      font-weight: 600;
    }
    .health-pill.degraded {
      background: rgba(220, 38, 38, 0.15);
      color: #f87171;
      border-color: rgba(248, 113, 113, 0.3);
    }
    .health-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }

    .tenant-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(255, 255, 255, 0.07);
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid var(--border-dark);
      font-size: 0.85rem;
    }
    .tenant-bar label {
      color: #94a3b8;
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 600;
    }
    .tenant-select {
      background: #0f172a;
      color: white;
      border: 1px solid var(--border-dark);
      border-radius: 4px;
      padding: 3px 6px;
      font-size: 0.8rem;
    }

    /* Tab Navigation */
    nav.tab-nav {
      background: #1e293b;
      padding: 0 1.5rem;
      display: flex;
      gap: 0.5rem;
      overflow-x: auto;
      border-bottom: 1px solid var(--border);
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: #94a3b8;
      padding: 0.85rem 1.1rem;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      border-bottom: 3px solid transparent;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: #f1f5f9;
    }
    .tab-btn.active {
      color: #38bdf8;
      border-bottom-color: #38bdf8;
    }

    /* Main Container */
    main.content-area {
      flex: 1;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem;
    }

    .tab-pane {
      display: none;
    }
    .tab-pane.active {
      display: block;
    }

    /* Cards & Grids */
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: #1e293b;
    }
    .card-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }

    /* Form Elements */
    .form-group {
      margin-bottom: 1rem;
    }
    .form-group label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: #475569;
      margin-bottom: 0.35rem;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .form-control, select.form-control, textarea.form-control {
      width: 100%;
      padding: 0.6rem 0.8rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.9rem;
      font-family: inherit;
      background: #ffffff;
      transition: border-color 0.15s;
    }
    .form-control:focus {
      outline: none;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }
    textarea.form-control {
      resize: vertical;
      min-height: 80px;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      padding: 0.6rem 1.1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.15s;
    }
    .btn-primary {
      background: var(--primary);
      color: white;
    }
    .btn-primary:hover {
      background: var(--primary-hover);
    }
    .btn-secondary {
      background: #f1f5f9;
      color: #334155;
      border-color: #cbd5e1;
    }
    .btn-secondary:hover {
      background: #e2e8f0;
    }
    .btn-success {
      background: var(--success);
      color: white;
    }
    .btn-success:hover {
      background: #15803d;
    }
    .btn-danger {
      background: var(--danger);
      color: white;
    }
    .btn-danger:hover {
      background: #b91c1c;
    }
    .btn-warning {
      background: var(--warning);
      color: white;
    }
    .btn-warning:hover {
      background: #b45309;
    }
    .btn-sm {
      padding: 0.3rem 0.6rem;
      font-size: 0.78rem;
    }

    /* Badges & Tables */
    .badge {
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .badge-primary { background: var(--primary-light); color: var(--primary); }
    .badge-success { background: var(--success-light); color: var(--success); }
    .badge-warning { background: var(--warning-light); color: var(--warning); }
    .badge-danger { background: var(--danger-light); color: var(--danger); }
    .badge-muted { background: #f1f5f9; color: #64748b; }

    table.data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      text-align: left;
    }
    table.data-table th {
      background: #f8fafc;
      padding: 0.7rem 0.9rem;
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 700;
      color: #64748b;
      border-bottom: 1px solid var(--border);
    }
    table.data-table td {
      padding: 0.75rem 0.9rem;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    table.data-table tr:hover td {
      background: #fafafa;
    }

    .mono {
      font-family: var(--font-mono);
      font-size: 0.82rem;
    }

    /* Modal / Drawer */
    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(2px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    .modal-overlay.active {
      display: flex;
    }
    .modal-box {
      background: #ffffff;
      border-radius: 10px;
      max-width: 750px;
      width: 100%;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    }
    .modal-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .modal-header h3 {
      font-size: 1.1rem;
      color: #0f172a;
    }
    .modal-close {
      background: none;
      border: none;
      font-size: 1.3rem;
      cursor: pointer;
      color: #64748b;
    }
    .modal-body {
      padding: 1.25rem;
      overflow-y: auto;
      flex: 1;
    }
    .modal-footer {
      padding: 0.85rem 1.25rem;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      background: #f8fafc;
    }

    /* Toast */
    #toast-container {
      position: fixed;
      bottom: 1.5rem;
      right: 1.5rem;
      z-index: 2000;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .toast {
      padding: 0.75rem 1.2rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 500;
      color: white;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.15);
      animation: fadeIn 0.2s ease;
      min-width: 250px;
      max-width: 400px;
    }
    .toast-success { background: #16a34a; }
    .toast-error { background: #dc2626; }
    .toast-info { background: #0284c7; }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Metrics Bar */
    .metrics-banner {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 1.25rem;
    }
    .metric-card {
      flex: 1;
      min-width: 140px;
      background: white;
      padding: 0.9rem 1.1rem;
      border-radius: 8px;
      border: 1px solid var(--border);
    }
    .metric-value {
      font-size: 1.6rem;
      font-weight: 800;
      color: #0f172a;
    }
    .metric-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      font-weight: 600;
      color: #64748b;
    }

    /* Citation Badge */
    .citation-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-family: var(--font-mono);
      cursor: pointer;
      margin-right: 4px;
      margin-top: 4px;
    }
    .citation-badge:hover {
      background: #e2e8f0;
      border-color: #94a3b8;
    }
  </style>
</head>
<body>

  <!-- Top Global Header -->
  <header class="global-header">
    <div class="brand">
      <div class="brand-icon">🛡️</div>
      <div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span class="brand-title">AEGIS-DocIntel</span>
          <span class="brand-badge">Intelligence Workbench</span>
        </div>
      </div>
    </div>

    <div class="header-controls">
      <div id="healthIndicator" class="health-pill">
        <span class="health-dot"></span>
        <span id="healthText">Probing system...</span>
      </div>

      <div class="tenant-bar">
        <label for="tenantSelect">Active Tenant:</label>
        <select id="tenantSelect" class="tenant-select" onchange="switchTenant(this.value)">
          <option value="dev-default-tenant">default-tenant (Admin/Reviewer)</option>
          <option value="dev-tenant-alpha">tenant-alpha (Multi-tenant A)</option>
          <option value="dev-tenant-beta">tenant-beta (Multi-tenant B)</option>
          <option value="custom">Custom Token / Key...</option>
        </select>
      </div>
    </div>
  </header>

  <!-- Navigation Tabs -->
  <nav class="tab-nav">
    <button class="tab-btn active" onclick="showTab('tab-documents')">📄 Documents</button>
    <button class="tab-btn" onclick="showTab('tab-ask')">💬 Ask & Evidence</button>
    <button class="tab-btn" onclick="showTab('tab-intelligence')">🧠 Fact Intelligence & Compare</button>
    <button class="tab-btn" onclick="showTab('tab-reviews')">⚖️ Governance & Reviews</button>
    <button class="tab-btn" onclick="showTab('tab-jobs')">⚙️ Background Jobs</button>
    <button class="tab-btn" onclick="showTab('tab-diagnostics')">🩺 Diagnostics & API</button>
  </nav>

  <!-- Content Area -->
  <main class="content-area">

    <!-- TAB 1: DOCUMENTS -->
    <section id="tab-documents" class="tab-pane active">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Upload & Ingest Document</div>
          <div class="card-desc">Supported: PDF, DOCX, TXT, HTML. Documents are indexed into chunks with layout coordinates.</div>
          <form id="uploadForm" onsubmit="handleUpload(event)">
            <div class="form-group">
              <input type="file" id="fileInput" class="form-control" accept=".pdf,.docx,.txt,.html" required>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <span id="uploadProgress" class="mono" style="font-size:0.8rem; color:#64748b;"></span>
              <button type="submit" class="btn btn-primary" id="uploadBtn">Upload & Ingest</button>
            </div>
          </form>
        </div>

        <div class="card">
          <div class="card-title">Tenant Ingestion Status</div>
          <div class="card-desc">Current document repository summary for the active tenant.</div>
          <div class="metrics-banner">
            <div class="metric-card">
              <div class="metric-value" id="docCountStat">0</div>
              <div class="metric-label">Ingested Docs</div>
            </div>
            <div class="metric-card">
              <div class="metric-value" id="chunkCountStat">0</div>
              <div class="metric-label">Total Chunks</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <span>Tenant Document Repository</span>
          <button class="btn btn-secondary btn-sm" onclick="loadDocuments()">↻ Refresh List</button>
        </div>
        <div style="overflow-x: auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Document ID</th>
                <th>Filename</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Pages</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="documentsTableBody">
              <tr><td colspan="6" style="text-align:center; color:#94a3b8; padding:2rem;">Loading documents...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 2: ASK & EVIDENCE -->
    <section id="tab-ask" class="tab-pane">
      <div class="card">
        <div class="card-title">Evidence-Grounded Question & Answering</div>
        <div class="card-desc">Ask questions strictly grounded in ingested documents. The engine generates answers with verifiable citations and abstains when evidence is insufficient.</div>

        <div class="form-group">
          <label>Target Document Scope</label>
          <select id="askDocScope" class="form-control">
            <option value="">All Tenant Documents</option>
          </select>
        </div>

        <div class="form-group">
          <label>Question</label>
          <textarea id="questionInput" class="form-control" placeholder="e.g. What are the key termination conditions and notice periods?"></textarea>
        </div>

        <div style="display:flex; gap:0.5rem; margin-bottom:1rem; flex-wrap:wrap;">
          <span style="font-size:0.75rem; color:#64748b; align-self:center;">Examples:</span>
          <button class="btn btn-secondary btn-sm" onclick="setQuestion('What are the payment terms and due dates?')">Payment terms</button>
          <button class="btn btn-secondary btn-sm" onclick="setQuestion('What is the governing law and jurisdiction?')">Governing law</button>
          <button class="btn btn-secondary btn-sm" onclick="setQuestion('What is the liability limitation or cap?')">Liability cap</button>
        </div>

        <button class="btn btn-primary" id="askBtn" onclick="handleAsk()">Query Document Engine</button>
      </div>

      <div id="answerResultCard" class="card" style="display:none;">
        <div class="card-title">
          <span>Grounded Answer</span>
          <span id="answerStatusBadge" class="badge"></span>
        </div>
        <div id="answerText" style="margin-bottom:1rem; line-height:1.6; white-space:pre-wrap;"></div>

        <div id="citationsBlock" style="margin-top:1rem; border-top:1px solid var(--border); padding-top:0.75rem;">
          <div style="font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:0.5rem;">Citations & Evidence Links:</div>
          <div id="citationsList"></div>
        </div>

        <div id="warningsBlock" style="margin-top:0.75rem; display:none;">
          <div class="badge badge-warning" id="warningsText"></div>
        </div>
      </div>
    </section>

    <!-- TAB 3: FACT INTELLIGENCE & COMPARE -->
    <section id="tab-intelligence" class="tab-pane">
      <div class="grid-2">
        <!-- Fact Extraction -->
        <div class="card">
          <div class="card-title">Structured Fact Extraction</div>
          <div class="card-desc">Extract schema-validated typed entities (amounts, dates, clauses) with precise character and page evidence.</div>

          <div class="form-group">
            <label>Select Document</label>
            <select id="extractDocSelect" class="form-control"></select>
          </div>

          <div class="form-group">
            <label>Target Schema</label>
            <select id="extractSchemaSelect" class="form-control">
              <option value="contract_terms">contract_terms (Parties, effective dates, obligations)</option>
              <option value="financial_metrics">financial_metrics (Revenue, EBITDA, currency)</option>
              <option value="general">general (Entities, dates, identifiers)</option>
            </select>
          </div>

          <div class="form-group">
            <label>Optional Subject Entity Filter</label>
            <input type="text" id="extractSubjectInput" class="form-control" placeholder="e.g. Acme Corp">
          </div>

          <button class="btn btn-primary" onclick="handleExtractFacts()">Extract Facts</button>
        </div>

        <!-- Cross-Document Comparison -->
        <div class="card">
          <div class="card-title">Cross-Document Comparison</div>
          <div class="card-desc">Compare facts across two versions or agreements. Discrepancies are highlighted with source provenance.</div>

          <div class="form-group">
            <label>Left Document (Base)</label>
            <select id="compareDocLeft" class="form-control"></select>
          </div>

          <div class="form-group">
            <label>Right Document (Variant/Target)</label>
            <select id="compareDocRight" class="form-control"></select>
          </div>

          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-primary" onclick="handleCompareDocuments()">Compare Documents</button>
            <button class="btn btn-secondary" onclick="handleDetectConflicts()">Detect All Discrepancies</button>
          </div>
        </div>
      </div>

      <!-- Extraction Results -->
      <div id="factsResultCard" class="card" style="display:none;">
        <div class="card-title">
          <span>Extracted Structured Facts</span>
          <span id="factCountBadge" class="badge badge-primary"></span>
        </div>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Attribute</th>
                <th>Value</th>
                <th>Unit/Period</th>
                <th>Confidence</th>
                <th>Evidence Quote</th>
              </tr>
            </thead>
            <tbody id="factsTableBody"></tbody>
          </table>
        </div>
      </div>

      <!-- Comparison Results -->
      <div id="compareResultCard" class="card" style="display:none;">
        <div class="card-title">
          <span>Cross-Document Comparison Matrix</span>
          <span id="compareSummaryBadge" class="badge badge-primary"></span>
        </div>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Subject & Attribute</th>
                <th>Left Document Value</th>
                <th>Right Document Value</th>
                <th>Status</th>
                <th>Difference Summary</th>
              </tr>
            </thead>
            <tbody id="compareTableBody"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: HUMAN-IN-THE-LOOP REVIEWS -->
    <section id="tab-reviews" class="tab-pane">
      <div class="metrics-banner">
        <div class="metric-card">
          <div class="metric-value" id="revTotalStat">0</div>
          <div class="metric-label">Total Cases</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="revDecidedStat">0</div>
          <div class="metric-label">Decided</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="revApproveRateStat">0%</div>
          <div class="metric-label">Approval Rate</div>
        </div>
        <div class="metric-card">
          <div class="metric-value" id="revCorrectionRateStat">0%</div>
          <div class="metric-label">Correction Rate</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <div style="display:flex; align-items:center; gap:10px;">
            <span>Governance Review Queue</span>
            <select id="reviewStatusFilter" class="form-control" style="width:auto; padding:3px 8px; font-size:0.8rem;" onchange="loadReviews()">
              <option value="">All Statuses</option>
              <option value="pending" selected>Pending Review</option>
              <option value="in_review">In Review</option>
              <option value="approved">Approved</option>
              <option value="corrected">Corrected</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="loadReviews()">↻ Refresh Queue</button>
        </div>

        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Document</th>
                <th>Subject / Attribute</th>
                <th>Inferred Fact</th>
                <th>Status</th>
                <th>Version</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="reviewsTableBody">
              <tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:2rem;">No review items found for current filter.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 5: BACKGROUND JOBS -->
    <section id="tab-jobs" class="tab-pane">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Submit Asynchronous Job</div>
          <div class="card-desc">Queue long-running document ingestion, extraction, or reports via the durable idempotent job queue.</div>
          <div class="form-group">
            <label>Job Type</label>
            <select id="jobTypeSelect" class="form-control">
              <option value="ingest_document">ingest_document</option>
              <option value="extract_facts">extract_facts</option>
              <option value="compare_documents">compare_documents</option>
              <option value="generate_report">generate_report</option>
            </select>
          </div>
          <div class="form-group">
            <label>Resource / Document ID</label>
            <input type="text" id="jobResourceId" class="form-control" placeholder="Target document ID or batch ID">
          </div>
          <div class="form-group">
            <label>Idempotency Key (Optional)</label>
            <input type="text" id="jobIdempotencyKey" class="form-control" placeholder="e.g. job-req-12345">
          </div>
          <button class="btn btn-primary" onclick="handleSubmitJob()">Queue Background Job</button>
        </div>

        <div class="card">
          <div class="card-title">Job Worker Operations</div>
          <div class="card-desc">The job subsystem provides bounded exponential retries, crash recovery, and dead-letter queue isolation.</div>
          <div style="font-size:0.85rem; color:#475569; line-height:1.6;">
            <p><strong>States:</strong> <span class="badge badge-muted">queued</span> → <span class="badge badge-warning">running</span> → <span class="badge badge-success">succeeded</span> or <span class="badge badge-danger">failed</span></p>
            <p style="margin-top:0.5rem;"><strong>Execution Guarantee:</strong> At-least-once with idempotent deduplication keying.</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <span>Active & Historical Background Jobs</span>
          <button class="btn btn-secondary btn-sm" onclick="loadJobs()">↻ Refresh Jobs</button>
        </div>
        <div style="overflow-x:auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Type</th>
                <th>Resource ID</th>
                <th>Status</th>
                <th>Attempt</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="jobsTableBody">
              <tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:2rem;">Loading jobs...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 6: DIAGNOSTICS & SYSTEM API -->
    <section id="tab-diagnostics" class="tab-pane">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>Liveness & Readiness Probes</span>
            <button class="btn btn-secondary btn-sm" onclick="checkHealthProbes()">Check Probes</button>
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem;">
            <div>
              <div style="font-size:0.8rem; font-weight:700; color:#64748b;">LIVENESS PROBE (/health/live):</div>
              <pre id="livenessJson" class="mono" style="background:#f1f5f9; padding:0.6rem; border-radius:4px; font-size:0.8rem; margin-top:0.25rem;">Checking...</pre>
            </div>
            <div>
              <div style="font-size:0.8rem; font-weight:700; color:#64748b;">READINESS PROBE (/health/ready):</div>
              <pre id="readinessJson" class="mono" style="background:#f1f5f9; padding:0.6rem; border-radius:4px; font-size:0.8rem; margin-top:0.25rem;">Checking...</pre>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">OpenAPI & Engineering Endpoints</div>
          <div class="card-desc">Interactive documentation and developer interfaces.</div>
          <div style="display:flex; flex-direction:column; gap:0.5rem;">
            <a href="/docs" target="_blank" class="btn btn-secondary" style="justify-content:flex-start;">📘 Swagger UI Documentation (/docs)</a>
            <a href="/redoc" target="_blank" class="btn btn-secondary" style="justify-content:flex-start;">📑 ReDoc Interface (/redoc)</a>
            <a href="/openapi.json" target="_blank" class="btn btn-secondary" style="justify-content:flex-start;">📄 OpenAPI JSON Specification (/openapi.json)</a>
            <a href="/metrics" target="_blank" class="btn btn-secondary" style="justify-content:flex-start;">📊 Prometheus Metrics Endpoint (/metrics)</a>
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- Chunk Inspection Modal -->
  <div id="chunkModal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 id="modalDocTitle">Document Chunks</h3>
        <button class="modal-close" onclick="closeModal('chunkModal')">&times;</button>
      </div>
      <div class="modal-body" id="modalDocBody"></div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('chunkModal')">Close</button>
      </div>
    </div>
  </div>

  <!-- Review Decision Modal -->
  <div id="decisionModal" class="modal-overlay">
    <div class="modal-box">
      <div class="modal-header">
        <h3 id="decisionModalTitle">Review Decision</h3>
        <button class="modal-close" onclick="closeModal('decisionModal')">&times;</button>
      </div>
      <div class="modal-body">
        <div id="decisionCaseDetails" style="margin-bottom:1rem; padding:0.75rem; background:#f8fafc; border-radius:6px; font-size:0.85rem;"></div>

        <div class="form-group">
          <label>Review Decision Action</label>
          <select id="decisionActionSelect" class="form-control" onchange="toggleCorrectionInput(this.value)">
            <option value="approved">Approve Fact</option>
            <option value="corrected">Correct Fact Value</option>
            <option value="rejected">Reject Fact</option>
            <option value="request_evidence">Request Additional Evidence</option>
          </select>
        </div>

        <div id="correctionBlock" class="form-group" style="display:none;">
          <label>Corrected Value</label>
          <input type="text" id="correctedValueInput" class="form-control" placeholder="Enter corrected value">
        </div>

        <div class="form-group">
          <label>Decision Rationale (Required)</label>
          <textarea id="decisionRationaleInput" class="form-control" placeholder="Provide audit justification for this decision..."></textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="closeModal('decisionModal')">Cancel</button>
        <button class="btn btn-primary" onclick="submitDecisionAction()">Submit Decision</button>
      </div>
    </div>
  </div>

  <!-- Toast Container -->
  <div id="toast-container"></div>

  <!-- Workbench Logic -->
  <script>
    // State
    let currentAuthToken = localStorage.getItem("aegis_token") || "dev-default-tenant";
    let cachedDocuments = [];
    let currentActiveReview = null;

    // Toast Notification System
    function showToast(message, type = "info") {
      const container = document.getElementById("toast-container");
      const toast = document.createElement("div");
      toast.className = `toast toast-${type}`;
      toast.textContent = message;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 250);
      }, 4000);
    }

    // Authenticated API Helper
    async function apiFetch(endpoint, options = {}) {
      const headers = options.headers || {};
      if (currentAuthToken) {
        if (currentAuthToken.startsWith("aegis-") || currentAuthToken.length === 64) {
          headers["X-API-Key"] = currentAuthToken;
        } else {
          headers["Authorization"] = `Bearer ${currentAuthToken}`;
        }
      }
      options.headers = headers;

      try {
        const response = await fetch(endpoint, options);
        if (response.status === 401) {
          showToast("Authentication required or expired token.", "error");
        }
        return response;
      } catch (err) {
        showToast(`Network error: ${err.message}`, "error");
        throw err;
      }
    }

    // Tab Navigation
    function showTab(tabId) {
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      const targetPane = document.getElementById(tabId);
      if (targetPane) targetPane.classList.add("active");
      const clickedBtn = Array.from(document.querySelectorAll(".tab-btn")).find(b => b.getAttribute("onclick")?.includes(tabId));
      if (clickedBtn) clickedBtn.classList.add("active");

      // Auto-load tab data
      if (tabId === "tab-documents") loadDocuments();
      if (tabId === "tab-reviews") { loadReviews(); loadReviewMetrics(); }
      if (tabId === "tab-jobs") loadJobs();
      if (tabId === "tab-diagnostics") checkHealthProbes();
    }

    // Tenant Switcher
    function switchTenant(token) {
      if (token === "custom") {
        const custom = prompt("Enter Bearer Token or API Key:", currentAuthToken);
        if (custom) {
          currentAuthToken = custom;
          localStorage.setItem("aegis_token", custom);
        }
      } else {
        currentAuthToken = token;
        localStorage.setItem("aegis_token", token);
      }
      showToast(`Active credentials switched: ${currentAuthToken}`, "info");
      loadDocuments();
      if (document.getElementById("tab-reviews").classList.contains("active")) {
        loadReviews();
        loadReviewMetrics();
      }
    }

    // System Health Probe
    async function checkSystemHealth() {
      const pill = document.getElementById("healthIndicator");
      const text = document.getElementById("healthText");
      try {
        const res = await fetch("/health/live");
        if (res.ok) {
          pill.className = "health-pill";
          text.textContent = "System: Online";
        } else {
          pill.className = "health-pill degraded";
          text.textContent = `System: Degraded (${res.status})`;
        }
      } catch (e) {
        pill.className = "health-pill degraded";
        text.textContent = "System: Offline";
      }
    }

    // Modal Helpers
    function openModal(id) {
      document.getElementById(id).classList.add("active");
    }
    function closeModal(id) {
      document.getElementById(id).classList.remove("active");
    }

    // TAB 1: Ingestion & Documents
    async function handleUpload(e) {
      e.preventDefault();
      const fileInput = document.getElementById("fileInput");
      if (!fileInput.files || !fileInput.files[0]) return;

      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file);

      const progress = document.getElementById("uploadProgress");
      const btn = document.getElementById("uploadBtn");
      progress.textContent = "Uploading & processing...";
      btn.disabled = true;

      try {
        const res = await apiFetch("/v1/documents/upload", {
          method: "POST",
          body: formData,
        });

        if (res.ok) {
          const doc = await res.json();
          showToast(`Document uploaded: ${doc.filename || doc.doc_id}`, "success");
          fileInput.value = "";
          loadDocuments();
        } else {
          const err = await res.json().catch(() => ({}));
          showToast(`Upload failed: ${err.detail || res.statusText}`, "error");
        }
      } finally {
        progress.textContent = "";
        btn.disabled = false;
      }
    }

    async function loadDocuments() {
      const tbody = document.getElementById("documentsTableBody");
      try {
        const res = await apiFetch("/v1/documents");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const docs = data.items || data.documents || [];
        cachedDocuments = docs;

        // Update stats
        document.getElementById("docCountStat").textContent = docs.length;
        let totalChunks = docs.reduce((acc, d) => acc + (d.chunk_count || d.num_chunks || 0), 0);
        document.getElementById("chunkCountStat").textContent = totalChunks;

        // Update scope selectors across tabs
        updateDocumentSelectors(docs);

        if (docs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#94a3b8; padding:2rem;">No documents found for this tenant. Upload a file above.</td></tr>`;
          return;
        }

        tbody.innerHTML = docs.map(doc => `
          <tr>
            <td class="mono" title="${doc.doc_id}">${doc.doc_id.substring(0, 8)}...</td>
            <td><strong>${escapeHtml(doc.filename || "Untitled")}</strong></td>
            <td><span class="badge ${doc.status === 'processed' || doc.status === 'ready' ? 'badge-success' : 'badge-warning'}">${doc.status}</span></td>
            <td>${doc.chunk_count || doc.num_chunks || 0}</td>
            <td>${doc.page_count || doc.pages || 1}</td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="viewDocumentChunks('${doc.doc_id}', '${escapeHtml(doc.filename)}')">Chunks</button>
              <button class="btn btn-primary btn-sm" onclick="selectForExtraction('${doc.doc_id}')">Extract</button>
              <button class="btn btn-secondary btn-sm" onclick="selectForAsk('${doc.doc_id}')">Ask</button>
            </td>
          </tr>
        `).join("");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#dc2626; padding:2rem;">Failed to load documents: ${err.message}</td></tr>`;
      }
    }

    function updateDocumentSelectors(docs) {
      const askScope = document.getElementById("askDocScope");
      const extractSelect = document.getElementById("extractDocSelect");
      const leftSelect = document.getElementById("compareDocLeft");
      const rightSelect = document.getElementById("compareDocRight");

      const optionsHtml = docs.map(d => `<option value="${d.doc_id}">${escapeHtml(d.filename)} (${d.doc_id.substring(0,6)})</option>`).join("");

      if (askScope) askScope.innerHTML = `<option value="">All Tenant Documents</option>` + optionsHtml;
      if (extractSelect) extractSelect.innerHTML = optionsHtml || `<option value="">Upload document first</option>`;
      if (leftSelect) leftSelect.innerHTML = optionsHtml;
      if (rightSelect) rightSelect.innerHTML = optionsHtml;
      if (rightSelect && docs.length > 1) rightSelect.selectedIndex = 1;
    }

    async function viewDocumentChunks(docId, filename) {
      document.getElementById("modalDocTitle").textContent = `Chunks for: ${filename}`;
      const body = document.getElementById("modalDocBody");
      body.innerHTML = "Loading chunk elements...";
      openModal("chunkModal");

      try {
        const res = await apiFetch(`/v1/documents/${docId}/chunks`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const chunks = data.items || data.chunks || [];
        if (chunks.length === 0) {
          body.innerHTML = "<p style='color:#64748b;'>No chunk elements indexed for this document.</p>";
          return;
        }
        body.innerHTML = chunks.map((c, i) => `
          <div style="border:1px solid var(--border); border-radius:6px; padding:0.75rem; margin-bottom:0.75rem; background:#ffffff;">
            <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem; font-size:0.75rem; color:#64748b;">
              <span class="mono">Chunk #${i + 1} (${c.chunk_id ? c.chunk_id.substring(0,8) : 'id'}) [${c.block_type || 'text'}]</span>
              <span>Page ${c.page_start || c.page_number || 1}</span>
            </div>
            <div style="font-size:0.85rem; line-height:1.5; color:#1e293b; white-space:pre-wrap;">${escapeHtml(c.text || '')}</div>
          </div>
        `).join("");
      } catch (err) {
        body.innerHTML = `<p style="color:#dc2626;">Error loading chunks: ${err.message}</p>`;
      }
    }

    function selectForExtraction(docId) {
      showTab("tab-intelligence");
      document.getElementById("extractDocSelect").value = docId;
    }
    function selectForAsk(docId) {
      showTab("tab-ask");
      document.getElementById("askDocScope").value = docId;
    }

    // TAB 2: Ask & Evidence
    function setQuestion(q) {
      document.getElementById("questionInput").value = q;
    }

    async function handleAsk() {
      const question = document.getElementById("questionInput").value.trim();
      if (!question) {
        showToast("Please enter a question.", "warning");
        return;
      }
      const scope = document.getElementById("askDocScope").value;
      const btn = document.getElementById("askBtn");
      btn.disabled = true;
      btn.textContent = "Querying documents...";

      const resultCard = document.getElementById("answerResultCard");
      const answerText = document.getElementById("answerText");
      const statusBadge = document.getElementById("answerStatusBadge");
      const citationsList = document.getElementById("citationsList");
      const warningsBlock = document.getElementById("warningsBlock");

      try {
        const bodyPayload = { question };
        if (scope) bodyPayload.document_ids = [scope];

        const res = await apiFetch("/v1/answers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(bodyPayload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        resultCard.style.display = "block";
        answerText.textContent = data.answer || "No text provided.";

        if (data.status === "abstained") {
          statusBadge.className = "badge badge-warning";
          statusBadge.textContent = "ABSTAINED (Insufficient Evidence)";
        } else {
          statusBadge.className = "badge badge-success";
          statusBadge.textContent = "ANSWERED (Evidence Grounded)";
        }

        const citations = data.citations || [];
        if (citations.length > 0) {
          citationsList.innerHTML = citations.map(c => `
            <span class="citation-badge" title="Evidence chunk: ${c.evidence_id}">
              📄 Doc: ${c.document_id.substring(0, 6)}... (Page ${c.page_number || 1})
            </span>
          `).join("");
        } else {
          citationsList.innerHTML = "<span style='font-size:0.8rem; color:#94a3b8;'>No explicit citations linked.</span>";
        }

        if (data.warnings && data.warnings.length > 0) {
          warningsBlock.style.display = "block";
          document.getElementById("warningsText").textContent = data.warnings.join("; ");
        } else {
          warningsBlock.style.display = "none";
        }
      } catch (err) {
        showToast(`Ask query failed: ${err.message}`, "error");
      } finally {
        btn.disabled = false;
        btn.textContent = "Query Document Engine";
      }
    }

    // TAB 3: Fact Extraction & Compare
    async function handleExtractFacts() {
      const docId = document.getElementById("extractDocSelect").value;
      if (!docId) {
        showToast("Please select a document first.", "warning");
        return;
      }
      const schemaName = document.getElementById("extractSchemaSelect").value;
      const subject = document.getElementById("extractSubjectInput").value.trim() || undefined;

      const card = document.getElementById("factsResultCard");
      const tbody = document.getElementById("factsTableBody");
      const badge = document.getElementById("factCountBadge");

      card.style.display = "block";
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:#64748b;">Extracting schema facts...</td></tr>`;

      try {
        const res = await apiFetch(`/v1/documents/${docId}/extract-facts`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ schema_name: schemaName, subject }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        const facts = data.facts || [];
        badge.textContent = `${facts.length} facts extracted`;

        if (facts.length === 0) {
          tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:#94a3b8;">No facts extracted for schema '${schemaName}'.</td></tr>`;
          return;
        }

        tbody.innerHTML = facts.map(f => {
          const ev = (f.evidence && f.evidence[0]) ? f.evidence[0].quoted_text : "";
          const conf = f.confidence != null ? Math.round(f.confidence * 100) + "%" : "N/A";
          return `
            <tr>
              <td><strong>${escapeHtml(f.subject || '')}</strong></td>
              <td><code>${escapeHtml(f.attribute || '')}</code></td>
              <td>${escapeHtml(String(f.value || f.raw_value || ''))}</td>
              <td>${escapeHtml(f.unit || '-')}</td>
              <td><span class="badge badge-primary">${conf}</span></td>
              <td style="max-width:300px; font-size:0.8rem; color:#475569;" title="${escapeHtml(ev)}">${escapeHtml(ev ? (ev.substring(0, 100) + '...') : '-')}</td>
            </tr>
          `;
        }).join("");
        showToast(`Extraction completed: ${facts.length} facts extracted.`, "success");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:#dc2626;">Extraction failed: ${err.message}</td></tr>`;
      }
    }

    async function handleCompareDocuments() {
      const leftDoc = document.getElementById("compareDocLeft").value;
      const rightDoc = document.getElementById("compareDocRight").value;
      if (!leftDoc || !rightDoc) {
        showToast("Please select two documents to compare.", "warning");
        return;
      }
      if (leftDoc === rightDoc) {
        showToast("Select two distinct documents for cross-comparison.", "warning");
        return;
      }

      const card = document.getElementById("compareResultCard");
      const tbody = document.getElementById("compareTableBody");
      const badge = document.getElementById("compareSummaryBadge");

      card.style.display = "block";
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#64748b;">Comparing structured facts...</td></tr>`;

      try {
        const res = await apiFetch("/v1/intelligence/compare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            left_document_id: leftDoc,
            right_document_id: rightDoc,
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        const comparisons = data.comparisons || [];
        const conflictsCount = (data.summary && data.summary.conflicts) || 0;
        badge.textContent = `${comparisons.length} attributes compared (${conflictsCount} conflicts)`;

        if (comparisons.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#94a3b8;">No shared attributes found between these two documents.</td></tr>`;
          return;
        }

        tbody.innerHTML = comparisons.map(c => {
          let statusBadgeClass = "badge-primary";
          if (c.status === "match") statusBadgeClass = "badge-success";
          if (c.status === "conflict" || c.status === "mismatch") statusBadgeClass = "badge-danger";

          return `
            <tr>
              <td><strong>${escapeHtml(c.subject || '')}</strong>: <code>${escapeHtml(c.attribute || '')}</code></td>
              <td>${escapeHtml(String(c.left_fact?.value ?? '-'))}</td>
              <td>${escapeHtml(String(c.right_fact?.value ?? '-'))}</td>
              <td><span class="badge ${statusBadgeClass}">${c.status.toUpperCase()}</span></td>
              <td style="font-size:0.8rem; color:#64748b;">${escapeHtml(c.difference_summary || '-')}</td>
            </tr>
          `;
        }).join("");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#dc2626;">Comparison failed: ${err.message}</td></tr>`;
      }
    }

    async function handleDetectConflicts() {
      const card = document.getElementById("compareResultCard");
      const tbody = document.getElementById("compareTableBody");
      const badge = document.getElementById("compareSummaryBadge");

      card.style.display = "block";
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#64748b;">Scanning tenant documents for contradictions...</td></tr>`;

      try {
        const res = await apiFetch("/v1/intelligence/conflicts");
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }
        const conflicts = await res.json();
        badge.textContent = `${conflicts.length} conflicting statements detected`;

        if (conflicts.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#16a34a;">No conflicting facts detected across tenant documents.</td></tr>`;
          return;
        }

        tbody.innerHTML = conflicts.map(cf => `
          <tr>
            <td><strong>${escapeHtml(cf.subject || '')}</strong>: <code>${escapeHtml(cf.attribute || '')}</code></td>
            <td colspan="2" style="font-size:0.85rem; color:#b91c1c;">${escapeHtml(cf.description || 'Conflict')}</td>
            <td><span class="badge badge-danger">CONFLICT</span></td>
            <td class="mono" style="font-size:0.75rem;">Docs: ${(cf.conflicting_document_ids || []).map(id => id.substring(0, 6)).join(", ")}</td>
          </tr>
        `).join("");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:#dc2626;">Failed: ${err.message}</td></tr>`;
      }
    }

    // TAB 4: Governance Reviews
    async function loadReviewMetrics() {
      try {
        const res = await apiFetch("/v1/reviews/metrics");
        if (res.ok) {
          const m = await res.json();
          document.getElementById("revTotalStat").textContent = m.total_items || 0;
          document.getElementById("revDecidedStat").textContent = m.decided_count || 0;
          document.getElementById("revApproveRateStat").textContent = Math.round((m.approval_rate || 0) * 100) + "%";
          document.getElementById("revCorrectionRateStat").textContent = Math.round((m.correction_rate || 0) * 100) + "%";
        }
      } catch (e) {}
    }

    async function loadReviews() {
      const tbody = document.getElementById("reviewsTableBody");
      const statusFilter = document.getElementById("reviewStatusFilter").value;
      const url = statusFilter ? `/v1/reviews?status=${statusFilter}` : `/v1/reviews`;

      try {
        const res = await apiFetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = data.items || [];

        if (items.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:2rem;">No review cases found for status: ${statusFilter || 'all'}.</td></tr>`;
          return;
        }

        tbody.innerHTML = items.map(it => {
          let badgeClass = "badge-warning";
          if (it.status === "approved") badgeClass = "badge-success";
          if (it.status === "corrected") badgeClass = "badge-primary";
          if (it.status === "rejected") badgeClass = "badge-danger";

          return `
            <tr>
              <td class="mono" title="${it.review_id}">${it.review_id.substring(0, 8)}...</td>
              <td class="mono">${(it.document_id || '').substring(0, 8)}...</td>
              <td><strong>${escapeHtml(it.subject || '')}</strong>: <code>${escapeHtml(it.attribute || '')}</code></td>
              <td>${escapeHtml(String(it.candidate_value || ''))}</td>
              <td><span class="badge ${badgeClass}">${it.status}</span></td>
              <td>v${it.version}</td>
              <td>
                <button class="btn btn-primary btn-sm" onclick="openDecisionModal('${it.review_id}', ${it.version}, '${escapeHtml(it.subject || '')}', '${escapeHtml(it.attribute || '')}', '${escapeHtml(String(it.candidate_value || ''))}', '${escapeHtml(it.evidence_quote || '')}')">Review</button>
              </td>
            </tr>
          `;
        }).join("");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#dc2626; padding:2rem;">Failed to load reviews: ${err.message}</td></tr>`;
      }
    }

    function openDecisionModal(reviewId, version, subject, attribute, candidateVal, quote) {
      currentActiveReview = { reviewId, version };
      document.getElementById("decisionModalTitle").textContent = `Review Case: ${subject} (${attribute})`;
      document.getElementById("decisionCaseDetails").innerHTML = `
        <p><strong>Candidate Fact:</strong> ${candidateVal}</p>
        <p style="margin-top:4px;"><strong>Evidence Quote:</strong> <em>"${quote || 'No explicit quote linked'}"</em></p>
      `;
      document.getElementById("decisionRationaleInput").value = "";
      document.getElementById("correctedValueInput").value = "";
      document.getElementById("decisionActionSelect").value = "approved";
      toggleCorrectionInput("approved");
      openModal("decisionModal");
    }

    function toggleCorrectionInput(action) {
      document.getElementById("correctionBlock").style.display = action === "corrected" ? "block" : "none";
    }

    async function submitDecisionAction() {
      if (!currentActiveReview) return;
      const action = document.getElementById("decisionActionSelect").value;
      const rationale = document.getElementById("decisionRationaleInput").value.trim();
      const correctedVal = document.getElementById("correctedValueInput").value.trim();

      if (!rationale) {
        showToast("Rationale is required for governance compliance.", "warning");
        return;
      }

      const payload = {
        action,
        expected_version: currentActiveReview.version,
        rationale,
      };
      if (action === "corrected") {
        payload.corrected_value = correctedVal;
      }

      try {
        const res = await apiFetch(`/v1/reviews/${currentActiveReview.reviewId}/decisions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }

        showToast(`Decision registered: ${action.toUpperCase()}`, "success");
        closeModal("decisionModal");
        loadReviews();
        loadReviewMetrics();
      } catch (err) {
        showToast(`Decision submission failed: ${err.message}`, "error");
      }
    }

    // TAB 5: Background Jobs
    async function handleSubmitJob() {
      const jobType = document.getElementById("jobTypeSelect").value;
      const resourceId = document.getElementById("jobResourceId").value.trim();
      const idempotencyKey = document.getElementById("jobIdempotencyKey").value.trim() || undefined;

      if (!resourceId) {
        showToast("Resource ID is required.", "warning");
        return;
      }

      const headers = { "Content-Type": "application/json" };
      if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;

      try {
        const res = await apiFetch("/v1/jobs", {
          method: "POST",
          headers,
          body: JSON.stringify({
            job_type: jobType,
            resource_id: resourceId,
            payload: {},
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        showToast(`Job queued successfully: ID ${data.job_id.substring(0, 8)}`, "success");
        document.getElementById("jobResourceId").value = "";
        loadJobs();
      } catch (err) {
        showToast(`Failed to queue job: ${err.message}`, "error");
      }
    }

    async function loadJobs() {
      const tbody = document.getElementById("jobsTableBody");
      try {
        const res = await apiFetch("/v1/jobs");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const jobs = data.items || [];

        if (jobs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#94a3b8; padding:2rem;">No background jobs recorded yet.</td></tr>`;
          return;
        }

        tbody.innerHTML = jobs.map(j => {
          let badgeClass = "badge-muted";
          if (j.status === "succeeded") badgeClass = "badge-success";
          if (j.status === "running") badgeClass = "badge-warning";
          if (j.status === "failed") badgeClass = "badge-danger";

          return `
            <tr>
              <td class="mono" title="${j.job_id}">${j.job_id.substring(0, 8)}...</td>
              <td><code>${j.job_type}</code></td>
              <td class="mono" title="${j.resource_id}">${j.resource_id.substring(0, 16)}...</td>
              <td><span class="badge ${badgeClass}">${j.status}</span></td>
              <td>${j.attempt}</td>
              <td style="font-size:0.75rem; color:#64748b;">${new Date(j.created_at).toLocaleTimeString()}</td>
              <td>
                ${j.status === 'running' || j.status === 'queued' ? `<button class="btn btn-danger btn-sm" onclick="cancelJob('${j.job_id}')">Cancel</button>` : ''}
                ${j.status === 'failed' || j.status === 'cancelled' ? `<button class="btn btn-secondary btn-sm" onclick="retryJob('${j.job_id}')">Retry</button>` : ''}
              </td>
            </tr>
          `;
        }).join("");
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:#dc2626; padding:2rem;">Failed to load jobs: ${err.message}</td></tr>`;
      }
    }

    async function cancelJob(jobId) {
      try {
        const res = await apiFetch(`/v1/jobs/${jobId}/cancel`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason: "User cancelled from workbench" }),
        });
        if (res.ok) {
          showToast(`Job cancelled: ${jobId.substring(0, 8)}`, "info");
          loadJobs();
        }
      } catch (e) {
        showToast(`Cancel failed: ${e.message}`, "error");
      }
    }

    async function retryJob(jobId) {
      try {
        const res = await apiFetch(`/v1/jobs/${jobId}/retry`, { method: "POST" });
        if (res.ok) {
          showToast(`Job retried: ${jobId.substring(0, 8)}`, "info");
          loadJobs();
        }
      } catch (e) {
        showToast(`Retry failed: ${e.message}`, "error");
      }
    }

    // TAB 6: Diagnostics
    async function checkHealthProbes() {
      const livenessPre = document.getElementById("livenessJson");
      const readinessPre = document.getElementById("readinessJson");

      try {
        const res1 = await fetch("/health/live");
        const json1 = await res1.json().catch(() => ({ status: res1.status }));
        livenessPre.textContent = JSON.stringify(json1, null, 2);
      } catch (e) {
        livenessPre.textContent = `Error: ${e.message}`;
      }

      try {
        const res2 = await fetch("/health/ready");
        const json2 = await res2.json().catch(() => ({ status: res2.status }));
        readinessPre.textContent = JSON.stringify(json2, null, 2);
      } catch (e) {
        readinessPre.textContent = `Error: ${e.message}`;
      }
    }

    // Utility: XSS Escaping
    function escapeHtml(text) {
      if (!text) return "";
      return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // Initialization
    window.addEventListener("DOMContentLoaded", () => {
      // Sync tenant select dropdown with stored credentials
      const select = document.getElementById("tenantSelect");
      if (select) {
        let found = false;
        for (let opt of select.options) {
          if (opt.value === currentAuthToken) {
            opt.selected = true;
            found = true;
            break;
          }
        }
        if (!found) {
          select.value = "custom";
        }
      }

      checkSystemHealth();
      setInterval(checkSystemHealth, 15000);
      loadDocuments();
    });
  </script>
</body>
</html>
"""
