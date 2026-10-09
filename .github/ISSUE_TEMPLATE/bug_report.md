---
name: Bug report
about: Something didn't work as expected
title: "[BUG] "
labels: ["bug"]
---

**What did you try to do?**
A clear and concise description of the task or pipeline step you attempted.

**What happened instead?**
A clear and concise description of what actually occurred, including unexpected behavior or error codes.

**Cold-start check**:
- [ ] Yes, this happened right after following the README's fresh install instructions.
- [ ] No, this occurred after the system had already been running / during deeper feature usage.
*(This distinction helps us isolate first-impression installation blockers from downstream logic issues).*

**Environment**
- OS: [e.g. Ubuntu 24.04, Windows 11, macOS 14]
- Python version: [e.g. 3.12.3, 3.13.0]
- Installed via:
  - [ ] `aegis-docprep` standalone package (`pip install aegis-docprep`)
  - [ ] Full monorepo: `requirements-core.txt`
  - [ ] Full monorepo: `requirements-core.txt` + `requirements-dev.txt`
  - [ ] Full monorepo: `requirements-core.txt` + `requirements-ml.txt`

**Steps to Reproduce**
1. Run command '...'
2. Pass input document '...'
3. See error

**Logs / Traceback**
```text
Paste terminal output, error logs, or traceback here
```
