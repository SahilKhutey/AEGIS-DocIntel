# 05 - Evaluator Onboarding Specification
1. Operator creates profile via `POST /v1/admin/evaluators`.
2. Operator issues high-entropy token via `POST /v1/admin/evaluators/{id}/invite`.
3. Evaluator accesses portal, reviews agreements, and submits acceptance.
4. Operator/Gateway issues 14-day evaluation license.
5. Client performs cryptographic challenge-response device binding.
6. Gateway grants short-lived authenticated session.
