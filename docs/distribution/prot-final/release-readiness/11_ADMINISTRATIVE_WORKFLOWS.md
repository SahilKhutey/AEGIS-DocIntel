# 11 - Administrative Workflows
- Restricted operator router: `/v1/admin/evaluators`, `/v1/admin/evaluation/*`.
- Strict RBAC: Requires `admin` role. Evaluators attempting access receive HTTP 403 Forbidden (`REL-013`).
