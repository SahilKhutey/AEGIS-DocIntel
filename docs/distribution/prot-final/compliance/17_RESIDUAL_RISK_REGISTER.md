# Residual Risk Register & Exception Log

## Evaluated Residual Risks
All identified compliance and security risks (`RSK-001` through `RSK-008`) have been mitigated to LOW residual severity through automated technical controls, sandbox isolation, and cryptographic verification.

Approved exceptions:
- `EXC-001`: Staging sandbox running on internal Docker bridge (`internal: true`).
- `EXC-002`: Anthropic Claude 30-day abuse monitoring buffer (anonymized excerpts only).
