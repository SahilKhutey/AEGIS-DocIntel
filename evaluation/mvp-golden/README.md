# AEGIS-DocIntel — MVP Golden Evaluation Dataset

Version-controlled synthetic test corpus for end-to-end document extraction, PII redaction, table preservation, and grounded RAG retrieval verification.

## Dataset Structure

- `manifest.json`: Root registry with cryptographic SHA-256 hashes of all test fixtures.
- `text/`: Clean synthetic input documents (contains zero customer or private data).
- `expected/`: Ground-truth expected extractions, tables, labeled PII entities, and grounded QA pairs.

## Verification

The integrity of this golden dataset is verified via automated SHA-256 checks:
```bash
python -c "import hashlib, json, pathlib; m = json.loads(pathlib.Path('evaluation/mvp-golden/manifest.json').read_text()); [(hashlib.sha256(pathlib.Path('evaluation/mvp-golden', d['path']).read_bytes()).hexdigest() == d['sha256']) for d in m['documents']]"
```
