# AEGIS-DocIntel — Launch Frequently Asked Questions (FAQ)

**Workstream:** `launch/product-hunt/listing`  
**Phase:** `PROT-FINAL-09`  

---

### Q1: How is AEGIS-DocIntel different from tools like ChatPDF or AskYourPDF?
**A:** Generic PDF chatbots treat PDFs as flat text strings, split them into arbitrary character chunks, and stuff the prompt. AEGIS reconstructs spatial layout geometry using Kahn's DAG reading-order algorithms, optimizes prompt context via submodular knapsack algorithms, provides exact bounding-box coordinate citations, and supports topological cross-document comparison across multiple files.

### Q2: Is my document data used to train AI foundation models?
**A:** **No.** Under our legal evaluation agreements and technical architecture, all document embeddings, text fragments, and queries are strictly tenant-isolated. Upstream LLM provider agreements explicitly prohibit training on API customer data.

### Q3: What document file formats are supported in the evaluation release?
**A:** The evaluation edition supports PDF (`application/pdf`), PNG (`image/png`), and JPEG (`image/jpeg`) up to 10 MB per document.

### Q4: How does the evaluation license work?
**A:** Every approved evaluator receives a unique, cryptographically signed Ed25519 license key. The key binds to your designated Windows machine via challenge-response hardware identification and operates with a daily quota (5 documents, 20 queries/day).

### Q5: Does AEGIS require an internet connection?
**A:** Yes. The evaluation client runs locally on Windows (providing UI and local proxying), while proprietary mathematical extraction, embedding, and upstream inference run securely on our isolated cloud gateway.

### Q6: Can I compare two different versions of the same document?
**A:** Yes. The "Document Comparison" workflow allows you to select two documents, align structural headings, and surface contradictions, modifications, and omissions.

### Q7: What are the minimum system requirements for the Windows evaluation client?
**A:** Windows 10/11 (64-bit), 4 GB RAM, 500 MB free disk space, and modern web browser (Edge, Chrome, or Firefox).

### Q8: What happens when my evaluation quota is exhausted?
**A:** Quotas reset automatically every 24 hours (20 queries/day, 5 active documents). If you are an academic researcher or technical team needing higher evaluation volume, submit a quota extension request through the feedback portal.

### Q9: How do I report bugs or security observations?
**A:** Use the in-app feedback modal (`/v1/evaluation/feedback`) or email `security@aegis-docintel.internal`. Security and P0 defect reports are routed with priority.

### Q10: How do I completely delete my data after evaluation?
**A:** Evaluators can trigger an automated deletion request via the portal (`/v1/evaluation/termination-request`). This executes a cascading cryptographic wipe across primary storage, vector embeddings, and cached results.
