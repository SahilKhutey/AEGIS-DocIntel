# AEGIS-DocIntel Evaluation Framework & Quality Benchmark

This directory provides the standardized evaluation suite and reproducible benchmark framework for **AEGIS-DocIntel** (P2 implementation).

## Overview

The evaluation suite validates the central propositions of the pre-LLM context compiler:
1. **Extraction Fidelity**: Accurate layout-aware reading order recovery for multi-column documents and structured table reconstruction.
2. **Context Packing Invariants**: Hard token budget limit enforcement, non-negative similarity functions, and greedy submodular knapsack approximation bounds.
3. **Privacy & Redaction Quality**: Quantified precision and recall on labeled PII entities, zero downstream secret leakage, and fail-closed security.
4. **Retrieval & Evidence Grounding**: Strict pre-retrieval tenant isolation, hybrid rank fusion (RRF), verified citation integrity, and clean abstention on unanswerable queries.

---

## Directory Structure

```text
evaluation/
├── README.md                           # Documentation and usage guide
├── datasets/
│   ├── manifest.json                   # Dataset slices and quality gate definitions
│   └── qa_eval_dataset.json            # Versioned ground-truth dataset (20+ labeled cases)
├── scripts/
│   ├── evaluate_extraction.py          # Reading order Kendall's tau and table cell F1
│   ├── evaluate_packing.py             # Knapsack budget violations and approximation bounds
│   ├── evaluate_privacy.py             # Precision, recall, and downstream secret leakage
│   ├── evaluate_retrieval.py           # MRR, Recall@5, nDCG@5, and abstention accuracy
│   └── run_all.py                      # Unified benchmark runner & regression gate CLI
└── reports/
    └── baseline_report.json            # Generated benchmark results artifact
```

---

## Metric Definitions & Formulas

### 1. Document Extraction Fidelity
- **Kendall's Tau ($\tau$)**: Measures topological sort agreement between reconstructed reading order and ground-truth order:
  $$\tau = \frac{C - D}{\frac{1}{2} n (n - 1)}$$
  where $C$ is the number of concordant pairs and $D$ is discordant pairs. $\tau \ge 0.80$ is required.
- **Table Cell F1**: Harmonic mean of table row/column cell association precision and recall. Gate: $\text{F1} \ge 0.90$.

### 2. Context Packing Invariants
- **Available Context Budget ($B$)**:
  $$B = W - T_{\text{instructions}} - T_{\text{query}} - T_{\text{reserved\_output}} - T_{\text{overhead}}$$
- **Token Budget Violation Rate**: Must be strictly $0.0\%$. $\sum_{i \in S} c_i \le B$ must hold for all selected sets $S$.
- **Approximation Ratio**: Compared against exhaustive combinatorial search $S^*$ on small instances ($n \le 8$):
  $$\frac{F(S_{\text{greedy}})}{F(S^*)} \ge \frac{1 - 1/e}{2} \approx 0.316$$

### 3. Privacy & PII Redaction
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$ (Gate: $\ge 0.85$)
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$ (Gate: $\ge 0.85$)
- **Downstream Secret Leakage**: Fraction of raw secrets (SSN, API keys, emails) appearing unredacted in output text. Gate: strictly $0.0\%$.
- **Fail-Closed Blocking**: Verifies that any unexpected scanner failure raises `PIIRedactionPolicyError` rather than releasing unredacted text.

### 4. Retrieval & Grounding
- **Mean Reciprocal Rank (MRR)**: Average inverse rank of the first relevant document:
  $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
  Gate: $\text{MRR} \ge 0.70$.
- **Recall@5**: Fraction of relevant chunks retrieved in top 5 items. Gate: $\ge 0.80$.
- **Normalized Discounted Cumulative Gain (nDCG@5)**: Evaluates graded relevance ranking against ideal ordering.
- **Abstention Accuracy**: Percentage of unanswerable queries where the system cleanly returns an abstention message without fabricating citations. Gate: strictly $100.0\%$.

---

## Running Benchmarks

### Unified Benchmark Runner
To run all evaluations and check quality gates:
```bash
python evaluation/scripts/run_all.py --fail-under-gates
```
This produces `evaluation/reports/baseline_report.json` and exits with code 1 if any gate fails.

### Individual Evaluators
```bash
python evaluation/scripts/evaluate_extraction.py
python evaluation/scripts/evaluate_packing.py
python evaluation/scripts/evaluate_privacy.py
python evaluation/scripts/evaluate_retrieval.py
```

### Automated Pytest Suite
```bash
pytest tests/test_evaluation_runner.py -v
```
