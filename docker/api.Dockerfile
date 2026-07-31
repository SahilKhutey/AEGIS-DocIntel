# ─────────────────────────────────────────────────────────────────────────────
# AEGIS API image — dev / prod parity. Single-stage image; small footprint.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AMDI_API_HOST=0.0.0.0 \
    AMDI_API_PORT=8000

WORKDIR /app

# System deps for PyMuPDF + audio libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libxml2-dev libffi-dev \
        tesseract-ocr libtesseract-dev \
        ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY README.md LICENSE ./

RUN pip install --upgrade pip hatchling hatch-vcs \
    && pip install ".[dev]"

EXPOSE 8000
EXPOSE 9090

# Default command: API. Workers use a separate image / entrypoint.
CMD ["python", "-m", "amdi", "serve", "--host", "0.0.0.0", "--port", "8000"]
