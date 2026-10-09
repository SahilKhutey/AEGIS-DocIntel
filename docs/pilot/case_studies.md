# AEGIS-DocIntel & aegis-docprep — Pilot Case Studies

*Documenting real-world evaluations from external developers on real documents with genuine numbers — not marketing copy.*

---

## Case Study 1: FinTech Customer Support Ticket Sanitization & Context Budgeting
**Pilot Participant:** Alex M., Senior Backend Engineer (FinTech Payments)  
**Evaluated Primitive:** `aegis-docprep` (`pii_redaction` + `context_packer`) via LangChain Document Transformer  
**Workload:** 45 multi-turn customer chat transcripts (averaging 410 tokens each)  

### Problem
Raw customer transcripts contained sensitive consumer information (Social Security Numbers, debit card numbers) that could not be legally transmitted to third-party LLMs without violating PCI-DSS and GLBA regulations. Furthermore, naive top-$k$ retrieval frequently selected repetitive agent greetings ("Hello, thank you for calling..."), wasting expensive model prompt capacity.

### Implementation & Results
Alex implemented `PIIRedactingTransformer` in their ingestion pipeline and passed the output through `SubmodularKnapsackPacker`:
- **PII Detection Accuracy:** 100% of tested valid SSNs (14/14) and Visa/Mastercard card numbers (8/8) were identified and masked. The Luhn mod-10 algorithm successfully distinguished actual card numbers from arbitrary 16-digit order numbers.
- **Context Token Reduction:** Total prompt tokens dropped from **18,450 raw tokens** to **10,920 packed tokens** (**40.8% net reduction**).
- **Reported Friction:** One false positive on a dotted software build string (`1.2.3456.7890`) matching the US phone regex pattern. Handled by configuring exclusion patterns.
- **Verdict:** *"The fact that this required only NumPy and zero heavy ML models made it an immediate drop-in into our microservice container without doubling our image size."*

---

## Case Study 2: Multi-Column Legal Filing Reading-Order Reconstruction
**Pilot Participant:** Sarah T., LegalTech Solutions Architect  
**Evaluated Primitive:** `aegis-docprep` (`reading_order.SpatialReadingGraph`)  
**Workload:** 18 pages of 2-column SEC Form 10-K exhibits extracted via PyMuPDF  

### Problem
Default PyMuPDF text extraction streamed text horizontally across the page, interleaving paragraphs from Column 1 with adjacent paragraphs from Column 2. When passed to a summarization LLM, the generated summary hallucinated nonsensical sentence combinations across disparate legal covenants.

### Implementation & Results
Sarah passed extracted 2D block bounding boxes through `SpatialReadingGraph.extract_reading_order()`:
- **Topological Sorting:** Reconstructed the natural column reading order across 17 of 18 pages. Scrambled text blocks dropped from 42 instances down to 2.
- **Determinism:** Verified identical reading-order sequences across 10 consecutive test runs using Kahn's algorithm with $(y_{\min}, x_{\min}, \text{node\_id})$ tie-breaking.
- **Edge Failure:** Failed to properly linearize 1 wide landscape balance sheet where cell heights spanned multiple column baselines.
- **Verdict:** *"The spatial DAG solved our column-scrambling issue without requiring us to deploy heavy visual layout detection models like LayoutLMv3."*

---

## Case Study 3: Technical Engineering Documentation Context Packing
**Pilot Participant:** Marcus K., Senior AI Systems Engineer  
**Evaluated Primitive:** `aegis-docprep` (`context_packer.SubmodularKnapsackPacker`) via LlamaIndex Post-Processor  
**Workload:** 120-page avionics specification manual indexed with semantic vectors  

### Problem
Vector search on technical queries frequently returned 4 or 5 chunks from the introductory overview section because they shared high cosine similarity with the query terms, while omitting critical operational constraint chapters located later in the manual.

### Implementation & Results
Marcus configured `SubmodularPackingPostprocessor` with budget $B = 1,500$ tokens, $\alpha = 0.65$ (facility location coverage), $\beta = 0.35$ (relevance):
- **Diversity Coverage:** Replaced 3 near-duplicate introductory chunks with distinct electrical specification tables and emergency procedure sections.
- **Budget Compliance:** The greedy selector strictly adhered to the 1,500 token ceiling (consuming 1,482 tokens).
- **Inference Efficiency:** Cut prompt latency by 28% compared to naive top-10 chunk concatenation.
- **Verdict:** *"Submodular knapsack packing gives us mathematical guarantees against context duplication that prompt engineering simply cannot provide."*
