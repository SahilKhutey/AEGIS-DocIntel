# AEGIS-DocIntel Evaluation Client — Quick Start Guide

**Version:** 1.0.0-beta.1  
**Target Platform:** Windows x64 (Windows 10 / 11)  

---

## 1. Prerequisites
- Windows 10 (Build 19041+) or Windows 11 (64-bit).
- 4 GB RAM minimum (8 GB recommended).
- 500 MB free disk space.
- Modern web browser (Microsoft Edge, Google Chrome, Mozilla Firefox).

---

## 2. Installation Options

### Option A: Windows Installer (`AEGIS-DocIntel-Setup.exe`)
1. Download `AEGIS-DocIntel-Setup.exe` from the authorized evaluation distribution link.
2. Double-click the installer. Follow the setup wizard prompts.
3. The installer installs AEGIS-DocIntel to `%LOCALAPPDATA%\Programs\AEGIS-DocIntel` and creates a desktop shortcut.

### Option B: Portable Package (`AEGIS-DocIntel-Portable.zip`)
1. Download `AEGIS-DocIntel-Portable.zip`.
2. Extract the archive contents into an authorized local directory (e.g. `C:\Tools\AEGIS-DocIntel`).
3. Ensure the extracted folder contains `AEGIS-DocIntel.ps1` and `config/client.json`.

---

## 3. First Launch & Activation
1. Launch AEGIS-DocIntel from the Start Menu shortcut or by running `.\AEGIS-DocIntel.ps1` in PowerShell.
2. The launcher initializes the loopback service (`127.0.0.1:3000`) and automatically opens your default browser.
3. On the welcome screen, enter your designated **Evaluation Activation Token** or click **Import Offline License** to select your `evaluation.lic` file.
4. Once verified, your device is bound to your evaluation profile, and the Document Intelligence Workbench opens.

---

## 4. First Workflow in 60 Seconds
1. **Upload Document:** Click **Upload Document** and select `assets/demo/documents/acme_financial_2025.pdf`.
2. **Review Structure:** View hierarchical headings and table grids reconstructed by Kahn's DAG reading order parser.
3. **Ask Grounded Question:** In the prompt composer, type: *"What was Acme Corporation's reported operating margin in Q3?"*
4. **Inspect Citations:** Click the `[1]` citation pill to highlight the exact bounding-box coordinates on the source document page.
