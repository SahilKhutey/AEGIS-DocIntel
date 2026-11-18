# 12 - Privacy & Data Handling
### Data Processing Guarantees
- **No LLM Training**: Evaluator document data is strictly excluded from third-party foundation model training (contractually verified with OpenAI and Anthropic commercial APIs).
- **Encryption**: AES-256 at rest, TLS 1.3 in transit.
- **Tenant Isolation**: Evaluator data is cryptographically segregated by `evaluator_id`. Cross-tenant access is impossible.
- **Retention**: Evaluation data is automatically purged 30 days after evaluation expiry or immediately upon termination request.
