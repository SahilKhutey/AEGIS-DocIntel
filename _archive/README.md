# Archived Legacy Trees

The historical development trees previously located in this folder (`AMDI-legacy`, `MDIE-legacy`, and `amdi-os-legacy`) have been consolidated into the canonical `src/` codebase and archived to Git history as part of Phase 4 (Architectural Deduplication).

- **Architectural Lineage & History:** See [`docs/history.md`](../docs/history.md) for full narrative, migration details, and provenance mapping.
- **Git History Access:** All historical trees, commit histories, and diffs remain permanently accessible via Git:

```bash
# View archive commits
git log -- _archive/

# Inspect or restore historical tree from a specific commit
git checkout 0146eca -- _archive/
```
