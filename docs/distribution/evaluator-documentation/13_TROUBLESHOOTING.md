# 13 - Troubleshooting
| Symptom | Probable Cause | Remediation |
| :--- | :--- | :--- |
| `ERR_AUTH_INVALID` | Session token expired | Re-authenticate in the client. |
| `ERR_DEVICE_LIMIT` | Machine fingerprint mismatch | Contact operator to release device binding. |
| `ERR_QUOTA_EXCEEDED` | Evaluator reached document or query limit | Request quota increase via feedback desk. |
| `ERR_GATEWAY_UNREACHABLE` | Network firewall blocking port 443 | Verify proxy allows `evaluate.aegis.corp`. |
| `ERR_FILE_UNSUPPORTED` | File type not in allowlist | Convert file to PDF or DOCX. |
