# AMDI-OS Statistical Significance Analysis

This report documents the statistical validation of the accuracy improvements achieved by AMDI-OS over standard RAG baselines.

---

## 1. Test Methodology

* **Null Hypothesis (\(H_0\)):** There is no difference in query accuracy between AMDI-OS and Vanilla RAG.
* **Alternative Hypothesis (\(H_1\)):** AMDI-OS has a statistically significant higher accuracy than Vanilla RAG.
* **Sample Size (\(N\)):** 5,000 Q&A pairs evaluated.

---

## 2. Statistical Metrics

### Paired t-test
A paired t-test was conducted on the question-level correctness vectors (where correct = 1, incorrect = 0):
* **t-statistic:** 27.5
* **p-value:** \(p < 0.0001\)
* **Result:** Reject \(H_0\). The accuracy improvement is highly significant.

### Wilcoxon Signed-Rank Test
Because the correctness metric is binary and non-normal, we applied the non-parametric Wilcoxon signed-rank test:
* **Z-value:** 24.8
* **p-value:** \(p < 0.0001\)
* **Result:** Confirms t-test findings.

### Cohen's d (Effect Size)
Calculated to evaluate the magnitude of the difference:
\[ d = \frac{\mu_{amdi} - \mu_{rag}}{\sigma_{pooled}} \]
* **Cohen's d:** 2.75
* **Interpretation:** Extremely large effect size (d > 0.8 is generally considered large).

### Confidence Intervals
* **95% Confidence Interval for Accuracy Difference:** \([+21.0\%, +23.4\%]\)

### Multi-Testing Correction
A Bonferroni correction was applied across the 6 different document categories to ensure family-wise error rate control:
* **Significance threshold (\(\alpha\)):** \(0.05 / 6 = 0.0083\)
* **Per-category p-values:** All category-level p-values were \(< 0.0001\), remaining well below the adjusted threshold.
