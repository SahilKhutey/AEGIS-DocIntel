# Archived Legacy Trees

The pre-rename historical code (`AMDI-legacy`, `MDIE-legacy`, and `amdi-os-legacy`) has been moved to the dedicated `archive/legacy-history` branch to keep the main working tree focused on the current canonical codebase.

- **Architectural Lineage & History:** See [`docs/history.md`](../docs/history.md) for full narrative, migration details, and provenance mapping.
- **Dedicated Archive Branch:** Access the complete pre-rename snapshot at any time:
  ```bash
  git checkout archive/legacy-history
  ```
- **Historical Git Commit Access:**
  ```bash
  # View archive history commits
  git log -- _archive/

  # Inspect or restore historical tree from commit 0146eca
  git checkout 0146eca -- _archive/
  ```
