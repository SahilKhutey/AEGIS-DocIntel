"""
AEGIS-DocIntel Evaluator Documentation Generator
PROT-FINAL-08: Workstream 08.06
Generates the complete evaluator documentation package (17 guides + agreements + notices).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_DIR = REPO_ROOT / "docs" / "distribution" / "evaluator-documentation"
DOC_DIR.mkdir(parents=True, exist_ok=True)

DOCS = {
    "00_README.md": """# AEGIS-DocIntel Controlled Evaluation Documentation
Welcome to the official documentation package for the **AEGIS-DocIntel Controlled Evaluation Release (v0.1.0)**.
This suite provides external evaluators, security reviewers, and enterprise architects with complete operational guidance for installing, verifying, activating, and operating the AEGIS client under controlled conditions.

### Package Contents
1. `01_PRODUCT_OVERVIEW.md`: System mission, architectural isolation, and evaluation goals.
2. `02_SYSTEM_REQUIREMENTS.md`: Supported Windows environments, hardware, and network prerequisites.
3. `03_DOWNLOAD_AND_INSTALLATION.md`: Step-by-step installation instructions for Windows 10/11 x64.
4. `04_PACKAGE_VERIFICATION.md`: Cryptographic checksum and Ed25519 signature validation procedures.
5. `05_ACCOUNT_AND_ACTIVATION.md`: Invitation acceptance, device binding, and license activation.
6. `06_FIRST_TIME_SETUP.md`: Guided first-run workflow with synthetic demonstration datasets.
7. `07_WORKSPACE_GUIDE.md`: Navigating workspaces, managing collections, and status indicators.
8. `08_DOCUMENT_UPLOAD_GUIDE.md`: Uploading authorized synthetic documents and validation rules.
9. `09_DOCUMENT_INTELLIGENCE_GUIDE.md`: Grounded query execution, multi-document comparison, and citations.
10. `10_SUPPORTED_FORMATS_AND_LIMITATIONS.md`: Parsing specifications, MIME allowlists, and known boundaries.
11. `11_USAGE_AND_QUOTA_GUIDE.md`: Understanding metering, document limits, queries, and reset schedules.
12. `12_PRIVACY_AND_DATA_HANDLING.md`: Data residency, LLM model training exclusions, and retention controls.
13. `13_TROUBLESHOOTING.md`: Common diagnostic codes, remediation paths, and connection issues.
14. `14_FAQ.md`: Frequently asked operational and security questions.
15. `15_FEEDBACK_AND_BUG_REPORTING.md`: Defect reporting workflow, triage severities (P0-P3), and diagnostics.
16. `16_SECURITY_REPORTING.md`: Dedicated vulnerability disclosure and confidential escalation channel.
17. `17_UNINSTALLATION_AND_DATA_DELETION.md`: Clean client removal and cascading cloud data erasure.
18. `EVALUATION_AGREEMENT.md`: Legal terms governing controlled non-commercial evaluation.
19. `PRIVACY_NOTICE.md`: Data processing notice detailing rights under DPDP 2023, GDPR, and CCPA.
20. `THIRD_PARTY_NOTICES.txt`: Attributions and open source licenses for client components.
""",

    "01_PRODUCT_OVERVIEW.md": """# 01 - Product Overview
AEGIS-DocIntel is a privacy-first, enterprise-grade document intelligence platform designed to extract, analyze, synthesize, and cross-reference complex multi-page documents with strict mathematical grounding and provenance.

### Core Architectural Separation
The evaluation release enforces an immutable boundary between:
- **Downloadable Client**: A compiled, lightweight Windows presentation layer and local proxy.
- **Public Evaluation Gateway**: The TLS-terminated gateway enforcing Ed25519 licensing, device authorization, rate limits, and quota metering.
- **Private Processing Engine**: The isolated backend executing parsing, vector embeddings, grounded reasoning, and LLM orchestration. Evaluators have zero direct access to private backend code or LLM credentials.
""",

    "02_SYSTEM_REQUIREMENTS.md": """# 02 - System Requirements
The AEGIS-DocIntel Controlled Evaluation Client is optimized for standard Windows enterprise environments.

### Supported Platforms
- **Operating System**: Windows 11 (22H2 or later) 64-bit, Windows 10 (21H2 or later) 64-bit.
- **Hardware Architecture**: x86_64 / AMD64.
- **Memory**: Minimum 4 GB RAM (8 GB recommended).
- **Disk Space**: 500 MB free storage for client assets and local cache.
- **Network Connectivity**: Outbound HTTPS (port 443) to `evaluate.aegis.corp`. No inbound ports required.
- **Privileges**: Standard user permissions (Administrator elevation NOT required).
""",

    "03_DOWNLOAD_AND_INSTALLATION.md": """# 03 - Download & Installation Guide
### Step 1: Obtain Authorized Download Link
Upon receiving an authorized invitation email from `evaluations@aegis.corp`, click the portal link to request your signed download token.

### Step 2: Download the Archive
The release portal issues a time-limited download URL valid for 15 minutes. Save `AEGIS-Evaluation-0.1.0.zip` to a local folder (e.g., `C:\\Tools\\AEGIS`).

### Step 3: Extract Package
Extract the archive using Windows Explorer or PowerShell:
```powershell
Expand-Archive -LiteralPath "AEGIS-Evaluation-0.1.0.zip" -DestinationPath "$HOME\\AEGIS-Evaluation"
```

### Step 4: Launch Client
Run `launcher\\start-aegis.ps1`. The local client proxy will start and open your default browser to `http://localhost:3000`.
""",

    "04_PACKAGE_VERIFICATION.md": """# 04 - Package Verification
Before launching, verify that your download has not been corrupted or tampered with.

### Checksum Verification
Compute the SHA-256 digest of your downloaded zip file:
```powershell
Get-FileHash -Algorithm SHA256 "AEGIS-Evaluation-0.1.0.zip"
```
Compare the output against the hash published in `release-manifest-0.1.0.json`.

### Cryptographic Signature Verification
The release manifest is cryptographically signed using Ed25519:
```powershell
powershell -ExecutionPolicy Bypass -File launcher\\verify-package.ps1
```
Expected output: `[+] Release manifest verified compliant with Ed25519 key ID aegis-release-ed25519-2026-01`.
""",

    "05_ACCOUNT_AND_ACTIVATION.md": """# 05 - Account & Activation Guide
### Step 1: Open Activation Screen
When launching the application for the first time, you will be presented with the **Activation & Device Registration** screen.

### Step 2: Enter Evaluation License Token
Paste the 14-day evaluation license code provided in your onboarding pack.

### Step 3: Device Binding Challenge
The client automatically derives a hardware-bound device identity and submits a cryptographic proof-of-possession challenge to the gateway.
Upon success, the device is registered (maximum 1 device per evaluation license).

### Step 4: Accept Terms
Review and accept the Evaluation Agreement and Privacy Notice to finalize activation.
""",

    "06_FIRST_TIME_SETUP.md": """# 06 - First-Time Setup & Guided Tour
AEGIS-DocIntel includes synthetic demonstration documents to allow evaluators to immediately test core workflows without uploading confidential enterprise files.

### Demonstration Datasets
- `demo-data/synthetic-invoices/`: Simulated vendor invoices for tabular extraction.
- `demo-data/synthetic-contracts/`: Simulated Master Services Agreements for clause analysis.

### First-Run Walkthrough
1. Navigate to **Workspaces** -> Select **Synthetic Demo Workspace**.
2. Click **Run Extraction** on `sample-invoice-01.txt`.
3. Observe extraction of vendor names, line items, and totals.
4. Open the **Intelligence Query** tab and ask: `"What are the payment terms?"`
5. Verify that the answer cites explicit source lines with zero hallucinations.
""",

    "07_WORKSPACE_GUIDE.md": """# 07 - Workspace Guide
Workspaces provide tenant-isolated document environments.

### Key Workspace Functions
- **Collection Organization**: Group related documents into distinct project binders.
- **Processing Status Indicators**:
  * `UPLOADED`: Document received by gateway.
  * `VALIDATING`: Document undergoing MIME and malware inspection.
  * `PROCESSING`: Document being parsed into structured tokens and vectors.
  * `COMPLETED`: Document indexed and ready for grounded query and cross-comparison.
  * `FAILED`: Document parsing failed; actionable error code provided.
""",

    "08_DOCUMENT_UPLOAD_GUIDE.md": """# 08 - Document Upload Guide
### Upload Rules
- Supported formats: PDF, DOCX, TXT, TIFF.
- Maximum file size: 25 MB per document.
- Maximum batch size: 10 documents per upload job.
- Only authorized non-classified documents or synthetic test files should be uploaded during evaluation.

### Content Inspection & Safety
All incoming files are scanned for prohibited script execution, malformed PDF objects, and executable macros prior to parsing.
""",

    "09_DOCUMENT_INTELLIGENCE_GUIDE.md": """# 09 - Document Intelligence Guide
AEGIS-DocIntel provides grounded question-answering and multi-document synthesis.

### Grounding & Citations
Every statement returned by the intelligence engine includes an interactive citation linking directly to the page number, bounding box, or line offset of the source document.
If a question cannot be answered from the uploaded corpus, the engine returns an explicit `UNGROUNDED_IN_CORPUS` notice rather than guessing.

### Cross-Document Comparison
Compare multiple agreements side-by-side to highlight indemnification clauses, governing laws, and term deviations.
""",

    "10_SUPPORTED_FORMATS_AND_LIMITATIONS.md": """# 10 - Supported Formats & Known Limitations
### Supported Formats
- **PDF**: Versions 1.4 through 2.0 (searchable text and scanned images with OCR).
- **DOCX**: Microsoft Word 2007+ documents.
- **TXT / Markdown**: UTF-8 plain text files.
- **TIFF**: Multi-page scanned business records.

### Evaluation Limitations
- OCR throughput: Up to 50 pages per job in evaluation tier.
- Password-protected/encrypted documents are rejected at intake.
- Maximum evaluation quota: 50 documents, 200 queries per 14-day cycle.
""",

    "11_USAGE_AND_QUOTA_GUIDE.md": """# 11 - Usage & Quota Guide
The evaluation tier enforces conservative quotas to ensure shared gateway stability:
- **Document Limit**: 50 documents total per evaluator.
- **Query Limit**: 200 intelligence queries per evaluation period.
- **Storage Limit**: 500 MB total processed document storage.

### Viewing Remaining Quota
Click the **Usage** icon in the client navigation bar to view real-time consumed and remaining allowances. When quota is exhausted, operations return a clear `QUOTA_EXHAUSTED` notification.
""",

    "12_PRIVACY_AND_DATA_HANDLING.md": """# 12 - Privacy & Data Handling
### Data Processing Guarantees
- **No LLM Training**: Evaluator document data is strictly excluded from third-party foundation model training (contractually verified with OpenAI and Anthropic commercial APIs).
- **Encryption**: AES-256 at rest, TLS 1.3 in transit.
- **Tenant Isolation**: Evaluator data is cryptographically segregated by `evaluator_id`. Cross-tenant access is impossible.
- **Retention**: Evaluation data is automatically purged 30 days after evaluation expiry or immediately upon termination request.
""",

    "13_TROUBLESHOOTING.md": """# 13 - Troubleshooting
| Symptom | Probable Cause | Remediation |
| :--- | :--- | :--- |
| `ERR_AUTH_INVALID` | Session token expired | Re-authenticate in the client. |
| `ERR_DEVICE_LIMIT` | Machine fingerprint mismatch | Contact operator to release device binding. |
| `ERR_QUOTA_EXCEEDED` | Evaluator reached document or query limit | Request quota increase via feedback desk. |
| `ERR_GATEWAY_UNREACHABLE` | Network firewall blocking port 443 | Verify proxy allows `evaluate.aegis.corp`. |
| `ERR_FILE_UNSUPPORTED` | File type not in allowlist | Convert file to PDF or DOCX. |
""",

    "14_FAQ.md": """# 14 - Frequently Asked Questions
**Q: Can I share my evaluation package with a colleague?**
A: No. Evaluation licenses are tied to your specific identity and single registered device. Colleague access requires a separate invitation.

**Q: Where are my uploaded documents processed?**
A: All document parsing and vector indexing occur on AEGIS secure cloud staging infrastructure. No processing is done locally on your machine.

**Q: How do I export my analysis findings?**
A: Navigate to any processed document and click **Export as JSON** or **Export as CSV**.
""",

    "15_FEEDBACK_AND_BUG_REPORTING.md": """# 15 - Feedback & Bug Reporting
We actively solicit your feedback to refine AEGIS-DocIntel before commercial availability.

### How to Submit Feedback
1. Click the **Feedback** button in the top navigation bar.
2. Select Category (`ACTIVATION`, `INSTALLATION`, `FUNCTIONAL`, `UX`, `PERFORMANCE`, etc.).
3. Choose Severity (`P0` through `P3`).
4. Describe the observed behavior and reproduction steps.
5. All submissions are automatically sanitized to prevent accidental leakage of sensitive tokens or credentials.
""",

    "16_SECURITY_REPORTING.md": """# 16 - Security Vulnerability Reporting
AEGIS-DocIntel maintains a zero-tolerance policy for security defects.

### Reporting Route
If you discover a potential security exposure, privilege escalation, or cross-tenant leakage:
- Email: `security-evaluation@aegis.corp`
- Priority: P0 / Emergency
- GPG Key: Available on release portal `security/pgp-key.asc`
- Response Commitment: Acknowledgement within 4 hours; preliminary triage within 24 hours.

Please do not submit security vulnerabilities through public issue trackers or unencrypted channels.
""",

    "17_UNINSTALLATION_AND_DATA_DELETION.md": """# 17 - Uninstallation & Data Deletion
### Client Removal
To remove the evaluation client from your Windows workstation:
1. Terminate running instances via `launcher\\stop-aegis.ps1`.
2. Delete the application folder (`$HOME\\AEGIS-Evaluation`).
3. Clear local temporary cache under `%APPDATA%\\AEGIS-DocIntel`.

### Cloud Data Deletion
To permanently delete all documents, vector embeddings, and search indices from the private engine:
Navigate to **Settings** -> **Request Data Erasure**, or call `POST /v1/evaluation/termination-request`.
All tenant records are irreversibly purged within 24 hours.
""",

    "EVALUATION_AGREEMENT.md": """# AEGIS-DocIntel Controlled Evaluation Agreement
**Version 1.0.0 (Effective November 2026)**

1. **Grant of Evaluation License**: Subject to terms herein, AEGIS grants Evaluator a non-exclusive, non-transferable, revocable license to access and test AEGIS-DocIntel solely for internal evaluation purposes.
2. **Restrictions**: Evaluator shall not reverse engineer, decompile, or disassemble the client or gateway; bypass licensing restrictions; or use the software in a production capacity.
3. **Data Usage**: Evaluator acknowledges that evaluation data is processed via cloud infrastructure and agrees to upload only synthetic or authorized non-confidential files.
4. **Warranty Disclaimer**: THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.
5. **Termination**: Either party may terminate evaluation at any time. Upon termination, client access is immediately revoked.
""",

    "PRIVACY_NOTICE.md": """# AEGIS-DocIntel Evaluation Privacy Notice
**Version 1.0.0 (Effective November 2026)**

This Privacy Notice explains how AEGIS processes personal and operational data during controlled evaluation releases.

1. **Data Collected**: Contact email, organization name, machine name, hardware fingerprint, and diagnostic logs.
2. **Purposes**: Device binding, quota accounting, security telemetry, and evaluation support.
3. **Model Training Exclusions**: Document contents and intelligence queries are NEVER used to train, retrain, or improve artificial intelligence foundation models.
4. **Data Subject Rights**: Evaluators may exercise access, rectification, or cascading erasure rights at any time via `privacy@aegis.corp`.
""",

    "THIRD_PARTY_NOTICES.txt": """AEGIS-DocIntel Third-Party Software Notices
============================================

This package includes software distributed under open source licenses:

1. FastAPI (MIT License) - Copyright (c) Sebastin Ramrez
2. Pydantic (MIT License) - Copyright (c) Samuel Colvin
3. PyMuPDF (AGPL-3.0 / Commercial) - Copyright (c) Artifex Software, Inc.
4. Cryptography (Apache-2.0 / BSD) - Copyright (c) The Python Cryptographic Authority
5. Uvicorn (BSD-3-Clause) - Copyright (c) Encode OSS Ltd.

Full text of licenses is available at https://evaluate.aegis.corp/licenses.
"""
}

for filename, content in DOCS.items():
    file_path = DOC_DIR / filename
    file_path.write_text(content.strip() + "\n", encoding="utf-8")

print(f"[+] Successfully generated {len(DOCS)} evaluator documentation files in {DOC_DIR}")
