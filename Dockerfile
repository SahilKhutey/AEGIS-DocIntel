# Multi-stage / Production Dockerfile for AEGIS-DocIntel
FROM python:3.12-slim

# System dependencies for PDF parsing, OCR, and health checking
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Create non-root user and directories
RUN useradd -m -u 1000 aegis && \
    mkdir -p /app/data /app/config/tiktoken && \
    chown -R aegis:aegis /app

WORKDIR /app

# Install dependencies
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Copy source code and config
COPY --chown=aegis:aegis src/ ./src/
COPY --chown=aegis:aegis backend/ ./backend/
COPY --chown=aegis:aegis config/ ./config/
COPY --chown=aegis:aegis openapi.json ./

USER aegis

EXPOSE 8000 9090

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
