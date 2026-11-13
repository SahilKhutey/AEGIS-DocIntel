# AEGIS-DocIntel — Intellectual Property Protection Strategy

**Classification:** Strategic Product & Legal Architecture  
**Release Target:** Product Hunt Launch  
**Version:** 1.1.0  

---

## 1. Strategic Objective

The central commercial goal of the Product Hunt launch is to allow developers, technical founders, and enterprise architects to **experience the full power of AEGIS-DocIntel within minutes**, while ensuring that:
1. Core mathematical IP (sheaf topology, submodular context packing) is never compromised.
2. Competitors cannot clone or redistribute the engine.
3. Open-source goodwill is maintained through legitimate standalone open-source utilities (`aegis-docprep`).
4. An effortless conversion funnel guides serious evaluators to commercial enterprise contracts.

---

## 2. The Dual-License Architecture

AEGIS-DocIntel employs a strict **Dual-License Architecture**:

```
+---------------------------------------------------------------+
|                      AEGIS-DocIntel Ecosystem                 |
+--------------------------------+------------------------------+
|     Open-Source Utility Tier   |    Proprietary Core Tier     |
|                                |                              |
|  • aegis-docprep               |  • Sheaf Topology Engine     |
|  • File parsing & normalization|  • Submodular Packer         |
|  • Public SDK interfaces       |  • Governance Engine         |
|  • CLI inspection tools        |  • Evaluation Gateway        |
|                                |  • Enterprise Workbench      |
|                                |                              |
|  License: Apache-2.0           |  License: Commercial / Eval  |
+--------------------------------+------------------------------+
```

### Why Permissive Open-Source for `aegis-docprep`?
- **Developer Trust & Adoption:** Developers are free to embed document parsing, markdown conversion, and node chunking into their workflows.
- **Top of Funnel:** Demonstrates engineering excellence and establishes an industry standard for structured document preparation.

### Why Proprietary Closed-Core for the Intelligence Engine?
- **Defensibility:** The algorithmic innovation (sheaf Laplacian decomposition, submodular knapsack entropy packing, and invariant contradiction detection) represents months of proprietary research and significant competitive moat.
- **Commercial Sustainability:** Enterprise customers license AEGIS for mission-critical auditability, air-gapped deployments, and custom mathematical representations.

---

## 3. The Hybrid Distribution Model

Rather than shipping an opaque, obfuscated backend container that can still be decompiled by a dedicated reverse-engineer, AEGIS uses a **Hardware-Independent Hybrid Cloud Architecture**:

1. **Client-Side:**
   - Shipped as lightweight Docker Compose containers (`web` and `proxy`).
   - All client JavaScript is minified, bundled, and stripped of source maps.
   - Evaluator runs the workbench on `localhost:3000`.
2. **Cloud-Side:**
   - Proprietary engines run in a private, air-gapped cloud environment.
   - Secured by the **AEGIS Evaluation Gateway**.
   - Enforces 256-bit Ed25519 asymmetric cryptographic license validation.
   - Strictly enforces server-side quotas: 5 documents, 20 queries/day, 5 comparisons/day.
   - Implements multi-tenant isolation, preventing IDOR or cross-session leakage.

---

## 4. Evaluator-to-Enterprise Conversion Funnel

The evaluation experience is engineered to naturally highlight the value of upgrading:
1. **Interactive Evaluation:** Evaluator tests ground-truth citations and contradiction detection using the synthetic corpus.
2. **Custom Ingestion:** Evaluator uploads up to 5 of their own documents to test retrieval fidelity.
3. **Graceful Quota Notification:** When daily limits are reached, the UI displays clear quota consumption metrics and a one-click inquiry button to request an Enterprise Proof-of-Concept.
4. **Enterprise Offering:**
   - On-premises & air-gapped deployment packages.
   - Unlimited documents and queries.
   - Direct database connectors (Postgres, Snowflake, S3).
   - Dedicated fine-tuned domain models and custom topological representations.
