# 03 - Download & Installation Guide
### Step 1: Obtain Authorized Download Link
Upon receiving an authorized invitation email from `evaluations@aegis.corp`, click the portal link to request your signed download token.

### Step 2: Download the Archive
The release portal issues a time-limited download URL valid for 15 minutes. Save `AEGIS-Evaluation-0.1.0.zip` to a local folder (e.g., `C:\Tools\AEGIS`).

### Step 3: Extract Package
Extract the archive using Windows Explorer or PowerShell:
```powershell
Expand-Archive -LiteralPath "AEGIS-Evaluation-0.1.0.zip" -DestinationPath "$HOME\AEGIS-Evaluation"
```

### Step 4: Launch Client
Run `launcher\start-aegis.ps1`. The local client proxy will start and open your default browser to `http://localhost:3000`.
