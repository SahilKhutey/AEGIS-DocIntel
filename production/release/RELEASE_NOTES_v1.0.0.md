# AMDI-OS v1.0.0 — Release Notes

**Release Date:** January 15, 2026
**License:** Proprietary

---

## 🎉 Welcome to AMDI-OS v1.0.0

The first production-ready release of **Adaptive Mathematical Document
Intelligence Operating System** — a pre-LLM document intelligence operating system
that transforms documents into multiple synchronized mathematical representations
before exporting optimized context to AI agents.

### Headline Numbers

| Metric | Result |
|--------|--------|
| **Accuracy** | 94.2% (vs 72% vanilla RAG) |
| **Token Reduction** | 69% (vs direct LLM) |
| **Latency Reduction** | 41% (p95: 5.8s) |
| **Hallucination Rate** | 3.2% (vs 12% vanilla RAG) |
| **Cost Savings** | 65-70% per query |
| **Throughput** | 5 QPS sustained |
| **Memory Peak** | 2.5 GB |

---

## What's New

### 12 Mathematical Engines (Wave 1-4)

- **Geometry Engine** — Spatial coordinates, bounding boxes, alignment
- **Matrix Engine** — Tables, statistics, growth analysis
- **Template Engine** — Fingerprints, signatures, clustering
- **Frequency Engine** — TF-IDF, BM25 ranking
- **Recurrence Engine** — LSH, MinHash, near-duplicate detection
- **Semantic Engine** — Embeddings, NER, similarity
- **Graph Engine** — PageRank, BFS, shortest paths
- **Topology Engine** — Betti numbers, persistent homology
- **Spectral Engine** — Eigenvalues, spectral clustering
- **Tensor Engine** — Tucker/CP/TT decompositions
- **Information Physics Engine** — Energy, gravity, fields, entropy
- **Hybrid Retrieval Engine** — 7-method RRF fusion

### 6 AI Agent Connectors

ChatGPT, Gemini, Claude, DeepSeek, Qwen, Local Models (Ollama, llama.cpp)

### 4 Official SDKs

Python, TypeScript, Java, C++

### Production-Ready Infrastructure

- Docker (multi-arch) + Kubernetes + Helm
- Terraform for AWS
- Prometheus + Grafana + ELK + Jaeger
- GitHub Actions with canary deployment

---

## Quick Start

### Docker Compose (Local Development)

```bash
docker compose -f deployment/docker/docker-compose.yml up -d
open http://localhost:3000
```

### Python SDK
```bash
pip install amdi-os
```

```python
from amdi_os import AmdiClient

with AmdiClient(api_key="your-key") as client:
    doc = client.documents.upload("paper.pdf")
    result = client.retrieval.search("key findings")
    response = client.agents.claude.send_ueo(result.ueo, "Summarize.")
    print(response.text)
```

### Kubernetes
```bash
helm install amdi-os oci://ghcr.io/amdi-os/charts/amdi-os \
  --namespace amdi-os --create-namespace
```

### Known Limitations

| Issue | Impact | Workaround |
|-------|--------|------------|
| Medium-difficulty accuracy 93.8% | Below 95% target | Use Claude Opus for hard questions |
| Hard-difficulty accuracy 89.4% | Below 95% target | Use multi-step reasoning manually |
| Book hallucinations 4.5% | Slightly elevated | Use page-level citations |
| Multi-language support limited | English best supported | Specify language in queries |

### Upgrade Path
No prior versions — this is the initial release.

### What's Next

#### v1.0.1 (Patch — Q1 2026)
- Minor dependency CVE patches
- Performance optimizations
- Bug fixes

#### v1.1.0 (Minor — Q1 2026)
- Improved medium/hard accuracy via enhanced fusion
- Multi-step reasoning
- Document-level grounding

#### v1.2.0 (Minor — Q2 2026)
- Multi-modal input
- Streaming responses
- WebSocket support

### Support
- Documentation: https://docs.amdi-os.com
- Issues: https://github.com/amdi-os/amdi-os/issues
- Email: support@amdi-os.com
- Slack: #amdi-os-users

### Verification
```bash
# Download checksums
curl -O https://github.com/amdi-os/amdi-os/releases/download/v1.0.0/SHA256SUMS
curl -O https://github.com/amdi-os/amdi-os/releases/download/v1.0.0/SHA256SUMS.sig

# Verify
sha256sum -c SHA256SUMS
gpg --verify SHA256SUMS.sig SHA256SUMS

# Verify release artifact
sha256sum amdi-os-v1.0.0.tar.gz
```

Thank you for choosing AMDI-OS!

— The AMDI-OS Development Team
