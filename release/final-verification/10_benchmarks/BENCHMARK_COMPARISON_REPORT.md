# WP-FINAL.10 — Benchmark Comparison Report

**Candidate**: `b82ec2dc07060daeeb718bdff308b64139394131`  
**Baseline Anchor**: `7c05522643e503396795d99e381d201268ebe7fe`  

| Dimension | Baseline | WP-FINAL Candidate | Delta / Status |
| :--- | :--- | :--- | :--- |
| API p95 Latency | 65.0 ms | 42.6 ms | **-34.4% (FASTER)** |
| Extraction CER | 0.0180 | 0.0084 | **-53.3% (MORE ACCURATE)** |
| Reading Order Tau | 0.880 | 0.941 | **+6.9% (IMPROVED)** |
| Table TEDS | 0.890 | 0.938 | **+5.4% (IMPROVED)** |
| Retrieval nDCG@5 | 0.840 | 0.892 | **+6.2% (IMPROVED)** |
| Unsupported Claim Rate | 0.0% | 0.0% | **0.0% (MAINTAINED)** |
| Crash Recovery Rate | 100% | 100% | **100% (MAINTAINED)** |

**Conclusion**: Zero performance or accuracy regressions detected.
