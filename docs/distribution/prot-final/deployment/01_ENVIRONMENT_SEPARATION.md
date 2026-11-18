# Environment Separation Specification (DEP-01)

## Environment Topology
Four distinct environments are maintained:
- **Development (`development`):** Local workstation engineering using synthetic documents and mock credentials.
- **Continuous Integration (`ci`):** GitHub Actions ephemeral test runners running automated quality gates and pytest suites against synthetic datasets.
- **Staging (`staging`):** Pre-release integration and adversarial security penetration testing environment mirroring production topology but isolated from production evaluator data.
- **Production (`production`):** Hardened evaluation platform serving authorized evaluators.

## Cross-Environment Invariants
1. **Zero Credential Sharing:** Staging secrets are cryptographically rejected in production (`DEP-TEST-007`).
2. **Isolated Networks:** Docker bridge networks in staging and production are completely segregated.
3. **Data Partitioning:** Synthetic data only in Development, CI, and Staging.
