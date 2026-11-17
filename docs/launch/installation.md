# AEGIS-DocIntel — Installation & Deployment Guide

This guide covers deploying the **Product Launch Edition (v1.2.0)** using Docker Compose or direct source installation.

---

## 1. Quickstart: Docker Compose (Recommended)

### Option A: Launch Edition Live Demo Sandbox
To run the preconfigured demo sandbox with pre-seeded documents and Nginx ingress:

```bash
# 1. Clone the repository
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel

# 2. Launch the Demo Compose stack
docker-compose -f deploy/docker-compose.demo.yml up --build -d

# 3. Open in your browser
# Web Workbench: http://localhost
# Direct API Health Probe: http://localhost/health
```

### Option B: Self-Hosted Production Stack
To run the full multi-tenant stack with Prometheus and Grafana monitoring:

```bash
# 1. Configure environment variables
cp .env.example .env

# Generate an RSA keypair for RS256 JWT auth
openssl genrsa -out jwt_private.pem 2048
openssl rsa -in jwt_private.pem -pubout -out jwt_public.pem

# 2. Launch the self-hosted stack
docker-compose -f deploy/docker-compose.yml up --build -d

# 3. Access interfaces:
# Web Workbench: http://localhost:3000
# Core API: http://localhost:8000
# Grafana Telemetry: http://localhost:3001
```

---

## 2. Direct Source Installation (Developers)

### Prerequisites
- Python 3.12+
- Node.js 20+ and npm / pnpm
- Poppler & Tesseract (for PDF rendering & OCR)

### Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-core.txt
pip install -e aegis-docprep

# Seed the demo dataset
python demo/scripts/seed_demo.py

# Run the API server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd web
npm install
npm run dev
# Workbench available at http://localhost:3000
```

---

## 3. Verifying the Deployment

Run the automated verification harness against your live deployment:

```bash
python demo/scripts/verify_demo.py --api-url http://localhost:8000 --output-json launch_verification.json
```
A successful run returns exit code `0` and passes all 6 verification categories.
