# AEGIS-DocIntel Private Core Engine Container
# PROT-FINAL-05: Workstream DEP-03 & DEP-10

FROM python:3.12-slim-bookworm AS base

# Install security updates and OCR / document parsing libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root engine user
RUN groupadd -g 10002 aegiseng && \
    useradd -u 10002 -g aegiseng -s /bin/false -m aegiseng

WORKDIR /app

# Copy dependency specifications
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Copy backend engine code
COPY src/ ./src/
COPY configs/ ./configs/

USER 10002:10002

# Internal port only; NEVER mapped to host ports in docker-compose
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/readiness || exit 1

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
