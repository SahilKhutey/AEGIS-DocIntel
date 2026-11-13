# AEGIS-DocIntel Demo Edition — Evaluator Walkthrough Guide

Welcome to the **AEGIS-DocIntel Product Hunt Evaluation Guide**!

This guide walks you through setting up, verifying, and evaluating AEGIS-DocIntel on your workstation using the downloadable Demo Edition package.

---

## 1. Quick Setup & Launch

### Step 1: Extract the Archive
Extract `AEGIS-DocIntel-Demo-Edition.zip` to a directory on your machine:
```powershell
Expand-Archive -Path AEGIS-DocIntel-Demo-Edition.zip -DestinationPath .\AEGIS-Demo
cd .\AEGIS-Demo
```

### Step 2: Verify Package Authenticity
Before running, verify that the package has not been altered:
```powershell
.\launcher\verify-package.ps1
```
You should see:
```text
[+] Manifest loaded. Package: AEGIS-DocIntel-Demo-Edition v1.1.0
[+] Verified 24 files successfully.
[+] Verifying evaluation license signature...
 [OK] Cryptographic signature valid.
[SUCCESS] All package components verified authentic and untampered.
```

### Step 3: Start the Workbench
Ensure **Docker Desktop** is running, then execute:
```powershell
.\launcher\start-demo.ps1
```
The launcher will start the containers and open `http://localhost:3000` in your default browser.

---

## 2. Guided Evaluation Workflows

### Workflow 1: Inspect Synthetic Corpus & Ground-Truth Citations
1. Open the workbench at `http://localhost:3000`.
2. Notice the pre-loaded synthetic documents in `demo-data/`:
   - `aegis_neural_hardware_spec_v1.txt`
   - `aegis_neural_hardware_spec_v2.txt`
   - `aegis_enterprise_governance_whitepaper.txt`
3. Navigate to **Ask AEGIS** and try these benchmark queries:
   - *"What is the peak FP32 compute performance?"*  
     -> Observe citation evidence highlighting the difference: 450 TFLOPS (v1.0) vs 620 TFLOPS (v2.0).
   - *"What is the unified SRAM cache size?"*  
     -> Observe the invariant check confirming 128 MB across all revisions.
   - *"Explain the cryptographic audit ledger integrity mechanism."*  
     -> Observe the exact citation referencing the SHA-256 hash chain and Genesis block.

### Workflow 2: Automated Cross-Document Contradiction Detection
1. Navigate to **Document Comparison**.
2. Select `aegis_neural_hardware_spec_v1.txt` as the baseline and `aegis_neural_hardware_spec_v2.txt` as the revision.
3. Click **Analyze Differences**.
4. AEGIS highlights:
   - **Critical Contradictions:** FP32 Compute (+37.7% increase), Thermal Design Power (220W vs 285W TDP).
   - **Structural Invariants:** Unified On-Die SRAM Cache (128 MB maintained).

### Workflow 3: Ingest Your Own Document
1. Navigate to **Documents** -> **Upload**.
2. Select a PDF, Markdown, or text file from your computer (up to 10 MB).
3. Inspect the extracted structured hierarchy, node breakdown, and citation previews.
4. Note: Evaluation accounts can ingest up to 5 concurrent documents.

---

## 3. Session Controls & Reset

- **Check Status & Remaining Quota:**
  ```powershell
  .\launcher\status-demo.ps1
  ```
- **Reset Demo Session to Clean State:**
  ```powershell
  .\launcher\reset-demo.ps1
  ```
- **Halt Containers Gracefully:**
  ```powershell
  .\launcher\stop-demo.ps1
  ```

---

## 4. Next Steps: Enterprise Licensing

Need unlimited ingestion, air-gapped on-premises deployment, or direct database connectors?

- **Website:** [https://aegis-docintel.io](https://aegis-docintel.io)
- **Enterprise Contact:** [sales@aegis-docintel.io](mailto:sales@aegis-docintel.io)
- **Open-Source Tools:** Explore `aegis-docprep` on GitHub for standalone document preparation.
