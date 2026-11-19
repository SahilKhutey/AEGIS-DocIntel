# AEGIS-DocIntel Evaluation Client — Troubleshooting Guide

**Version:** 1.0.0-beta.1  

---

## 1. Local Startup Issues

### Symptom: "Port 3000 already in use"
- **Cause:** Another local development server or application is currently bound to port 3000.
- **Resolution:** The AEGIS launcher automatically negotiates an available loopback port (e.g. 3002). If needed, specify an explicit port in `config/client.json`:
  ```json
  "network": { "local_frontend_port": 3050 }
  ```

### Symptom: "Installation integrity check failed"
- **Cause:** One or more essential distribution files (public key, license, documentation) were moved or deleted.
- **Resolution:** Re-extract the original `AEGIS-DocIntel-Portable.zip` or run the installer repair tool.

---

## 2. Network & Gateway Connectivity

### Symptom: "Gateway unavailable (HTTP 503)"
- **Cause:** The client cannot establish a secure connection with the Evaluation Gateway.
- **Resolution:**
  1. Confirm your workstation has outbound HTTPS access to `gateway_url` specified in `config/client.json`.
  2. If operating behind an enterprise TLS inspection proxy, configure custom corporate CA certificates in Windows Certificate Store.
  3. Verify the remote service status indicator at `https://status.aegis-docintel.internal`.

---

## 3. Processing & Extraction Issues

### Symptom: "Scanned PDF produced no extractable text"
- **Cause:** The uploaded document consists purely of raster image scans without a native text layer, and host OCR binaries are unavailable.
- **Resolution:** Ensure documents contain selectable text or pre-process with an authorized OCR utility before ingestion.

### Symptom: "HTTP 413: Content Too Large"
- **Cause:** The uploaded file exceeds the 10 MB evaluation limit.
- **Resolution:** Compress or split the document into sections within the 10 MB limit.
