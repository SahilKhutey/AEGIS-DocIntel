# 06 - First-Time Setup & Guided Tour
AEGIS-DocIntel includes synthetic demonstration documents to allow evaluators to immediately test core workflows without uploading confidential enterprise files.

### Demonstration Datasets
- `demo-data/synthetic-invoices/`: Simulated vendor invoices for tabular extraction.
- `demo-data/synthetic-contracts/`: Simulated Master Services Agreements for clause analysis.

### First-Run Walkthrough
1. Navigate to **Workspaces** -> Select **Synthetic Demo Workspace**.
2. Click **Run Extraction** on `sample-invoice-01.txt`.
3. Observe extraction of vendor names, line items, and totals.
4. Open the **Intelligence Query** tab and ask: `"What are the payment terms?"`
5. Verify that the answer cites explicit source lines with zero hallucinations.
