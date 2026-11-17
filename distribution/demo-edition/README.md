# AEGIS-DocIntel Demo Edition (v1.1.0)
### High-Performance Document Intelligence & Context Optimization Workbench

Welcome to the **AEGIS-DocIntel Evaluation Edition** for Product Hunt!

This self-contained downloadable package allows you to evaluate AEGIS-DocIntel locally on your computer with real, interactive workflows:
- **Inspect & Process Documents:** Ingest documents into structured hierarchical nodes with citation traceability.
- **Ask AEGIS:** Ask complex technical questions and receive evidence-grounded answers with exact quotes and confidence metrics.
- **Cross-Document Comparison:** Automatically detect contradictions, invariants, and specification drift across revisions.

---

## 🚀 Quick Start (Windows)

### Prerequisites:
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running.
- PowerShell 5.1+ (built into Windows 10/11).

### Step 1: Open PowerShell and Navigate to Package
```powershell
cd AEGIS-DocIntel-Demo-Edition
```

### Step 2: Launch the Demo
```powershell
.\launcher\start-demo.ps1
```
The script will:
1. Verify cryptographic SHA-256 integrity and evaluation license.
2. Spin up the lightweight containers via Docker Compose.
3. Automatically launch your default browser to `http://localhost:3000`.

### Step 3: Stop or Check Status
```powershell
.\launcher\status-demo.ps1   # Check status and remaining quota
.\launcher\stop-demo.ps1     # Gracefully stop containers
.\launcher\reset-demo.ps1    # Reset session documents
```

---

## 🐧 Quick Start (Linux / macOS / WSL)

```bash
cd AEGIS-DocIntel-Demo-Edition
chmod +x launcher/*.sh
./launcher/start-demo.sh
```

---

## 📂 Included Synthetic Evaluation Corpus
Located in `demo-data/`:
1. `aegis_neural_hardware_spec_v1.txt`: Baseline hardware revision (450 TFLOPS, 220W TDP, 128 MB cache).
2. `aegis_neural_hardware_spec_v2.txt`: Revised hardware revision (620 TFLOPS, 285W TDP, 128 MB cache).
3. `aegis_enterprise_governance_whitepaper.txt`: Cryptographic audit chaining & verification architecture.

---

## 🔒 Security & Evaluation Limits
This edition is licensed under the **AEGIS Evaluation License** (`LICENSE-EVALUATION.md`):
- 14-day evaluation period.
- Maximum 5 active document uploads.
- Maximum 20 Ask AEGIS queries per 24 hours.
- Maximum 5 cross-document comparisons per 24 hours.

For commercial licenses, air-gapped deployments, and enterprise source code access, contact:  
📧 **sales@aegis-docintel.io** | 🌐 **https://aegis-docintel.io**
