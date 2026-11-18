# Network Segmentation & Firewall Policy (DEP-04 / DEP-08)

## Zero-Trust Traffic Matrix
| Source | Destination | Protocol / Port | Policy | Authentication |
|:---|:---|:---|:---:|:---|
| Public Internet | Public Edge (Caddy) | TCP / 443, 80 | **ALLOW** | TLS 1.2 / TLS 1.3 |
| Public Internet | Private Engine | TCP / 8000 | **DENY** | Blocked at container edge |
| Public Internet | Database | TCP / 5432 | **DENY** | Blocked at container edge |
| Gateway | Private Engine | TCP / 8000 | **ALLOW** | HMAC-SHA256 Token |
| Private Engine | Database | TCP / 5432 | **ALLOW** | SCRAM-SHA-256 (`aegis_app`) |
| Private Engine | Approved LLMs | TCP / 443 | **ALLOW** | HTTPS Outbound Adapter |
| Private Engine | Arbitrary Outbound | Any | **DENY** | Egress Firewall Rule |
