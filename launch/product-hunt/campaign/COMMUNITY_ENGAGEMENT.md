# AEGIS-DocIntel — Community Engagement & Ethical Outreach Policy

**Workstream:** `launch/product-hunt/campaign`  
**Phase:** `PROT-FINAL-09`  

---

## 1. Ethical Launch Guarantees

Product Hunt explicitly forbids artificial vote manipulation, paid upvotes, and spam messaging. AEGIS commits unconditionally to:
- **Zero Vote Solicitation:** We never ask anyone to "upvote" our product. We ask people to try the tool, evaluate the workflow, and share honest feedback.
- **Zero Bot / Fake Engagement:** 100% of interactions and accounts are genuine human beings.
- **Personal Maker Account:** The launch is submitted from the founder's verified personal profile.
- **Transparent Disclosures:** We clearly disclose that AEGIS-DocIntel is currently in controlled evaluation (v0.1.0).

---

## 2. Meaningful Pre-Launch Community Engagement Channels

1. **Product Hunt Discussions:** Share engineering insights on layout-aware document chunking, submodular context packing, and topological data analysis.
2. **AI & ML Research Communities:** Discuss challenges in multi-document citation verification and spatial PDF parsing.
3. **Open Source & Developer Forums:** Share lessons learned from securing downloadable client packages against reverse-engineering.
4. **Academic Subreddits & Groups:** Engage with graduate researchers and analysts dealing with 100+ page literature reviews.

---

## 3. Communication Templates for Inquiries

### Template A: Inviting Early Technical Feedback
> "Hey [Name], I've been working on an open evaluation platform called AEGIS-DocIntel to address table scrambling and lost context when querying technical documents. I'd love to get your critical feedback on whether our layout-aware retrieval makes a difference in your workflow: [Link]. No votes needed—just looking for honest technical thoughts!"

### Template B: Responding to Technical Questions on PH
> "Great question! Standard RAG tools use simple sliding-window chunks which break when a table spans two pages. In AEGIS, we parse document bounding boxes, reconstruct reading order with a Kahn DAG, and optimize prompt tokens via submodular knapsack coverage. You can see the grounded citations directly in the evaluation build."
