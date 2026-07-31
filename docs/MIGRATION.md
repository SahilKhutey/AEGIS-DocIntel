# Migration Log — Sprint 2 (Deliverable E)

## Goal
Resolve the contradiction between the two visible module trees
(`backend/src/...` in one README, `src/...` in another) and remove the
prototype scaffolding acknowledged in the author's own public statements.

## What was unified
- Package namespace: `src/amdi/` (was: `src/` + `backend/src/`)
- Two READMEs → one consolidated `README.md`
- Two import styles → `import amdi.*` only
- Pinned `pyproject.toml` as the single source of truth
- Authoritative module → file mapping (see `docs/STRUCTURE.md`)

## What was removed
Confirmed prototype artefacts (no tests, no consumer, no docs):

| Removed                              | Reason                           |
| ------------------------------------ | -------------------------------- |
| `src/amdi/_legacy_prototypes/`      | Acknowledged by author           |
| `src/amdi/_stubs/`                  | One-off sketches                 |
| `docs/Architecture.md.local`        | Local dev-notes                  |
| `docs/Design.md.local`              | Local dev-notes                  |
| `requirements-dev-2025.txt`         | Snapshot, replaced by lock       |
| Any file matching `*_old.py`        | No git history + no consumer     |

If any of the above turn out to matter in your fork, `git revert` is the
recovery mechanism — the migration script preserves history.

## Compatibility window
`src/amdi/legacy_bridge.py` re-exports symbols under their old names for
**one minor version**. A `DeprecationWarning` is emitted on first import.
After that, the bridge is removed.

## How to verify

```bash
python scripts/verify_migration.py
pytest tests/migration -v
```
