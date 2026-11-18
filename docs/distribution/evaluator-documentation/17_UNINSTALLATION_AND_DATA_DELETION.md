# 17 - Uninstallation & Data Deletion
### Client Removal
To remove the evaluation client from your Windows workstation:
1. Terminate running instances via `launcher\stop-aegis.ps1`.
2. Delete the application folder (`$HOME\AEGIS-Evaluation`).
3. Clear local temporary cache under `%APPDATA%\AEGIS-DocIntel`.

### Cloud Data Deletion
To permanently delete all documents, vector embeddings, and search indices from the private engine:
Navigate to **Settings** -> **Request Data Erasure**, or call `POST /v1/evaluation/termination-request`.
All tenant records are irreversibly purged within 24 hours.
