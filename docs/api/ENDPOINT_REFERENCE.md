# Endpoint Reference

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

| Method | Path | Description | Roles |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT token | Public |
| `GET` | `/api/v1/documents` | List tenant documents | Viewer+ |
| `POST` | `/api/v1/documents` | Upload and process new document | Editor+ |
| `GET` | `/api/v1/documents/{id}`| Retrieve document details & status | Viewer+ |
| `DELETE`| `/api/v1/documents/{id}`| Trigger cascading document deletion | Editor+ |
| `POST` | `/api/v1/query` | Submit natural language query | Viewer+ |
| `POST` | `/api/v1/reports` | Generate intelligence report | Analyst+ |
