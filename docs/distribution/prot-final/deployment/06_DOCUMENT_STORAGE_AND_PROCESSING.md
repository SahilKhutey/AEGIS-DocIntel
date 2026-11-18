# Document Storage & Sandboxed Processing (DEP-05)

## Upload Controls
- **Max File Size:** 25 MB default ceiling.
- **Extension Allowlist:** `.pdf`, `.md`, `.txt`, `.json`, `.csv`.
- **Magic Bytes Inspection:** PDF (`%PDF-`), PNG, JPEG bytes verified before parsing.
- **Path Traversal Mitigation:** Rejection of `..`, absolute paths, and forbidden characters.

## Worker Sandboxing
- Processing runs in an isolated ephemeral scratch directory: `tempfile.mkdtemp(prefix="aegis_scratch_<tenant>_")`.
- Execution timeout enforced (10.0 seconds).
- Scratchpad is guaranteed to be deleted in a `finally:` block on both success and worker failure (`DEP-TEST-009`, `DEP-TEST-014`).
- Macro and embedded JavaScript execution is disabled.
