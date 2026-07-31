# Build & Distribution Reference

## One-shot local build

```bash
python -m pip install --upgrade pip build hatchling hatch-vcs hatch-fancy-pypi-readme
python -m build                # produces dist/amdi_os-<version>.tar.gz + .whl
```

## Versioning

Versions are derived from git tags via `hatch-vcs`.

```bash
git tag v0.2.0                 # tag a release
python -m build --sdist --wheel
```

The `__version__` constant is materialized to `src/amdi/_version.py` at build
time and excluded from VCS. On a source checkout (`pip install -e .`), it
defaults to `0.2.0.dev0`.

## Lint / type-check / format

```bash
ruff check src tests
ruff format --check src tests
mypy src
```

These mirror the CI pipeline exactly (same rules in `pyproject.toml`).

## Publishing (private index / internal)

```bash
python -m pip install twine
python -m twine upload --repository-url https://your-private-pypi dist/*
```

For internal distribution, consider `devpi`, `gitea`'s package registry, or
AWS CodeArtifact.

## Docker

```dockerfile
# Minimal example — full compose stack lands in Sprint 3
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["python", "-m", "amdi", "serve"]
```

## Pre-commit (recommended)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```
