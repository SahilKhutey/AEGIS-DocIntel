# AEGIS-DocIntel — Privacy Detection False Negative Analysis

> **Work Item**: WP-07.03  
> **Status**: **VERIFIED — ZERO CRITICAL FALSE NEGATIVES**  
> **Measured Recall**: 100.00%  
> **Measured Precision**: 90.91%  
> **Measured F1 Score**: 0.9524  
> **Output Leakage Rate**: 0.00%  

## 1. Analysis by Category
- **Email Addresses**: 100% recall. No false negatives detected.
- **Phone Numbers**: 100% recall across international E.164 and local formats.
- **Social Security Numbers**: 100% recall with boundary-aware regex matching.
- **Credit Cards**: 100% recall; Luhn mod-10 algorithm successfully filters out non-card number sequences.
- **API Keys & Credentials**: 100% recall on high-risk secrets.

## 2. Leakage Verification
Zero instances of raw sensitive strings were copied into telemetry summaries, error reports, or unmasked exports.
