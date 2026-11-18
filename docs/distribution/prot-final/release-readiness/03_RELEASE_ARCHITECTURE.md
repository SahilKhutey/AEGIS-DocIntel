# 03 - Target Release Architecture
### Trust Boundary Separation
```
+-------------------------------------------------------------------------+
| EVALUATOR WORKSTATION (Untrusted Environment)                           |
|  [AEGIS Launcher] -> [Compiled Frontend] -> [Local Reverse Proxy:3000]   |
+-------------------------------------------------------------------------+
                                    | HTTPS (TLS 1.3)
                                    v
+-------------------------------------------------------------------------+
| PUBLIC EVALUATION GATEWAY (DMZ)                                         |
|  - Ed25519 License Validation                                           |
|  - Device Binding Challenge & Presence                                  |
|  - Quota Metering & Atomic Hold                                         |
|  - Rate Limiting & Audit Telemetry                                      |
+-------------------------------------------------------------------------+
                                    | mTLS / Internal VPC
                                    v
+-------------------------------------------------------------------------+
| PRIVATE ENGINE API (Zero Public Access)                                 |
|  - Document Extraction & PyMuPDF Parsing                                |
|  - Vector Indexing & Semantic Search                                    |
|  - LLM Orchestration (Commercial APIs; Training Excluded)               |
+-------------------------------------------------------------------------+
```
