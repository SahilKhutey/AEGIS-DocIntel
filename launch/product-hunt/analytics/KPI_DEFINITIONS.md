# AEGIS-DocIntel — Launch KPI Definitions & Conversion Framework

**Workstream:** `launch/product-hunt/analytics`  
**Phase:** `PROT-FINAL-09`  

---

## 1. Conversion Funnel Mathematical Definitions

$$\text{Funnel: Product Hunt Discovery} \longrightarrow \text{Landing Page Visit} \longrightarrow \text{Signup} \longrightarrow \text{Activation} \longrightarrow \text{First Query} \longrightarrow \text{Retention}$$

| Conversion Step | Metric Name | Mathematical Formula | Target Benchmark |
| :--- | :--- | :--- | :--- |
| **Step 1: Visit-to-Signup** | Registration Rate ($R_{reg}$) | $$R_{reg} = \frac{\text{Unique Evaluation Registrations}}{\text{Unique Landing Page Visitors}} \times 100$$ | $\ge 15.0\%$ |
| **Step 2: Signup-to-Activation** | Activation Rate ($R_{act}$) | $$R_{act} = \frac{\text{Successful Device Activations}}{\text{Unique Evaluation Registrations}} \times 100$$ | $\ge 50.0\%$ |
| **Step 3: Activation-to-First-Use**| Workflow Adoption ($R_{adopt}$) | $$R_{adopt} = \frac{\text{Evaluators Completing } \ge 1 \text{ Workflow}}{\text{Successful Device Activations}} \times 100$$ | $\ge 70.0\%$ |
| **Step 4: Repeat Engagement** | Retention Rate ($R_{ret}$) | $$R_{ret} = \frac{\text{Active Evaluators in Day 3–7}}{\text{Evaluators Completing First Workflow}} \times 100$$ | $\ge 30.0\%$ |
| **Step 5: Feedback Conversion** | Feedback Rate ($R_{fb}$) | $$R_{fb} = \frac{\text{Submitted Feedback Forms}}{\text{Successful Device Activations}} \times 100$$ | $\ge 25.0\%$ |

---

## 2. Health & Quality Invariants

- **Activation SLA:** Time from download to successful device challenge-response $\le 180\text{ seconds}$.
- **Query Processing Latency:** Document retrieval and answer generation $\le 8.0\text{ seconds}$ for 20-page synthetic PDFs.
- **Zero-Error Invariant:** Total 5xx server errors on gateway $\le 0.1\%$ of total incoming requests.
