# AEGIS-DocIntel — Product Hunt First Maker Comment

**Field:** First Maker Comment  
**Platform Limit:** 5,000 characters  
**Tone:** Founder-led, transparent, technical, conversational  

---

### Approved First Maker Comment Copy

Hi Product Hunt! 👋

I'm Sahil, and I'm thrilled to share **AEGIS-DocIntel**, an AI-powered document intelligence platform built for people who deal with dense, technical, and high-stakes files.

### Why I Built AEGIS-DocIntel

If you've ever tried using standard PDF chatbots on real-world technical reports, scientific papers, or multi-page contracts, you've likely hit the same walls I did:
1. **Lost Geometry & Tables:** Most tools flatten documents into naive text dumps, scrambling multi-column layouts, financial tables, and mathematical notations.
2. **Context Window Waste:** Traditional RAG blindly stuffs random chunks into the LLM prompt, wasting valuable tokens on irrelevant fluff while omitting critical sections.
3. **The Multi-Document Void:** Comparing two 60-page revisions or finding contradictions between specifications requires opening 10 browser tabs and cross-referencing manually.
4. **Black-Box Hallucinations:** When an answer doesn't provide verifiable spatial coordinates, you cannot trust it for serious research or commercial work.

I wanted to explore a more connected, mathematically grounded approach.

---

### What AEGIS-DocIntel Does

AEGIS-DocIntel unifies the complete document lifecycle into one integrated evaluation workbench:
- 📑 **Layout-Aware Processing:** Reconstructs reading order using spatial Kahn's DAG algorithms and extracts hierarchical heading trees.
- 🎯 **Submodular Context Optimization:** Uses combinatorial knapsack optimization to maximize information coverage within fixed token budgets.
- 🔍 **Grounded Coordinate Citations:** Every retrieved fact is tethered to verified bounding box coordinates in the original PDF.
- ⚖️ **Cross-Document Analysis:** Surfaces agreements, contradictions, and revision deltas across multiple documents using topological concepts.
- 🛡️ **Zero-Leak Evaluation Architecture:** Downloadable Windows evaluation client backed by a remote private engine. Your uploads are strictly tenant-isolated and **never** used to train AI models.

---

### Where the Product Is Today

This is our **Controlled Evaluation Release (v0.1.0)**. We are deliberately launching on Product Hunt not to chase vanity metrics, but to invite researchers, technical analysts, and engineers into our evaluation programme.

Evaluation accounts include:
- 5 document processing capacity
- 10MB file size limit (PDF, PNG, JPEG)
- 20 queries / comparisons per day
- Asymmetric Ed25519 cryptographic licensing and single-device hardware binding

---

### What I'd Love Feedback On

Because I'm building this independently and iterating rapidly, your honest observations are invaluable:
1. **Document Processing:** How well does the parser preserve reading order and tables in your domain-specific files?
2. **Retrieval Precision:** Are the grounded answers relevant, and are the citations easy to audit?
3. **Multi-Doc Comparison:** What specific cross-document workflows (e.g. spec diffing, contract review, literature synthesis) would be most valuable to you?
4. **User Experience:** What friction points did you encounter during onboarding, activation, or first query?

Thank you so much for taking a look and exploring the evaluation! I'll be here all day to answer technical questions, discuss architecture, and hear your ideas. 🚀

— Sahil Khutey  
Creator of AEGIS-DocIntel
