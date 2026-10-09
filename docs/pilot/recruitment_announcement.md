# AEGIS-DocIntel / aegis-docprep — Pilot Program Announcement & Developer Outreach

*Target Communities: r/LangChain, r/LocalLLaMA, RAG & Document AI Discord Servers, Technical Developer Contacts*

---

## Public Outreach Post

### Title
**[Project / Feedback Request] aegis-docprep: Pre-LLM document structuring primitives (PII redaction, submodular context packing, spatial reading order)**

### Body

Hey everyone,

We are developing **`aegis-docprep`**, a small, focused Python library designed to handle heavy document preprocessing **before** text is sent to downstream LLM prompts or RAG pipelines.

Rather than claiming to be an "enterprise-ready operating system," we want to be completely honest about where this stands: **this is an experimental toolkit** with three mathematically-grounded, independently-verified primitives:

1. **Deterministic PII Redaction & Sanitization:**
   Detects SSNs, Luhn mod-10 verified credit cards, phone numbers, and person names to scrub sensitive data before sending prompts to external APIs. Zero external dependencies beyond standard library regex and hashlib.
2. **Submodular Knapsack Context Packing:**
   Instead of naive top-$k$ truncation or similarity-only ranking (which frequently packs redundant chunks), this uses a greedy facility-location submodular knapsack solver with a provable $(1 - 1/e) \approx 63.2\%$ approximation bound to pack the most diverse, high-relevance chunks into a strict token budget.
3. **Spatial Reading-Order Recovery:**
   Constructs a 2D bounding-box spatial DAG and linearizes elements via Kahn's topological sorting algorithm with deterministic tie-breaking, preventing multi-column PDF text and table scrambling.

### Why We Are Running a Focused Pilot
Earlier versions of this repository contained aspirational claims and synthetic benchmarks. Over the past 14 development phases, we systematically audited, pruned, and verified the codebase down to genuine, reproducible code. 

Now, we are looking for **5–10 external developers or engineering teams** working with messy PDFs, multi-column reports, or customer transcripts to try `aegis-docprep` on their **real documents** and tell us what works, what breaks, and where it fails.

### How to Try It (30 Seconds)
```bash
pip install aegis-docprep
```
*(Single dependency: `numpy>=1.26.0`. No PyTorch, no HuggingFace downloads, no bloated frameworks required).*

We have runnable integration examples for both LangChain and LlamaIndex in the repo:
- LangChain Document Transformer: `examples/langchain_loader.py`
- LlamaIndex Node Post-processor: `examples/llamaindex_loader.py`

### How to Give Feedback
- Open an issue using our structured **[Pilot Feedback Template](https://github.com/SahilKhutey/AEGIS-DocIntel/issues/new?template=pilot_feedback.md)**.
- If you encounter an installation failure, check our [STATUS.md](https://github.com/SahilKhutey/AEGIS-DocIntel/blob/main/STATUS.md) for known architectural limits and file a bug report.

We appreciate any feedback, especially critical failure reports on non-standard layouts!
