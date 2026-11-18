# 15 - Release and Rollback Procedure
- **Immutable Artifacts**: Packages cannot be overwritten in place; bugfixes increment version.
- **Rollback Invariants**: Rollback never restores revoked licenses, does not re-enable deactivated devices, and preserves all audit records (`REL-035`).
