# Vendoring the tiktoken cl100k_base Encoding

## Why

`src/ael/token_budget.py` needs the `cl100k_base` BPE encoding to count tokens
accurately. By default, `tiktoken` fetches this file over the network from
`openaipublic.blob.core.windows.net` on first use. In any network-restricted
deployment (air-gapped, VPC-egress-restricted, or firewalled — common for
AEGIS's regulated-industry target customers), that fetch fails, and prior to
the fix in Repository Audit Finding 2, this crashed the entire application at
startup.

`_load_encoding()` in `token_budget.py` now tries a locally vendored copy of
the encoding file first, before falling back to the network fetch, before
falling back to a degraded-mode approximate encoder. This document describes
how to produce that vendored file.

## Producing the vendored file (run once, with network access, e.g. in CI)

```bash
python3 -c "
import tiktoken, shutil
enc = tiktoken.get_encoding('cl100k_base')
# tiktoken caches the raw .tiktoken BPE file under its cache directory;
# locate and copy it into the vendored path the application expects.
import tiktoken.load as tl
cache_path = tl.load_tiktoken_bpe.__wrapped__ if hasattr(tl.load_tiktoken_bpe, '__wrapped__') else None
"
# Simpler, robust approach: use tiktoken's own cache directly.
python3 -c "
import os, tiktoken
os.environ.setdefault('TIKTOKEN_CACHE_DIR', '/tmp/tiktoken_cache')
enc = tiktoken.get_encoding('cl100k_base')
import glob
cached = glob.glob('/tmp/tiktoken_cache/*')
print('Cached blob(s):', cached)
"
```

tiktoken's cache stores the raw BPE ranks file under a hash-named filename
inside `TIKTOKEN_CACHE_DIR`. Copy that file to:

```
src/ael/_vendor/cl100k_base.tiktoken
```

## Where this runs

This should be a **build-time** step (Dockerfile `RUN` step, or a one-time CI
job artifact committed to the repository), never a runtime step — the whole
point is that a production container never needs network access for this at
startup. Add to the Dockerfile:

```dockerfile
# Vendor the tiktoken encoding at build time so runtime needs no network access.
RUN python3 scripts/vendor_tiktoken.py
```

## Verifying

```bash
AEGIS_TIKTOKEN_VENDOR_PATH=src/ael/_vendor/cl100k_base.tiktoken \
  python3 -c "from src.ael.token_budget import _ENC; print(type(_ENC).__name__)"
# Expected: tiktoken.core.Encoding (not _ApproximateEncoding)
```
