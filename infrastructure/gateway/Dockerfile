# AEGIS-DocIntel Evaluation Gateway Container
# PROT-FINAL-05: Workstream DEP-02 & DEP-10

FROM python:3.12-slim-bookworm AS base

# Install security updates and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Non-root unprivileged service user
RUN groupadd -g 10001 aegisgw && \
    useradd -u 10001 -g aegisgw -s /bin/false -m aegisgw

WORKDIR /app

# Copy dependency specifications
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# Copy gateway service code
COPY services/evaluation_gateway/ ./services/evaluation_gateway/
COPY src/gateway/ ./src/gateway/

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

ENTRYPOINT ["uvicorn", "services.evaluation_gateway.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
