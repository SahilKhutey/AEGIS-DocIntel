# AEGIS SRE Runbook

## AmdiHighErrorRate
1. Check `kubectl logs -l app=amdi --tail=300 | grep "http.error"`.
2. Correlate with deployment timeline (`kubectl rollout history`).
3. If ingest path: tail `/v1/documents/upload` p95; raise worker replicas.
4. If query path: check vector store health `/readyz → queue_ready`.

## AmdiHighLatency
1. Inspect `latency_ms=...` in `amdi.access` logs.
2. If `stage.fanout > 500ms`: warmup embedder (`python -m amdi doctor`).
3. If Redis spikes: check `redis-cli INFO clients`.

## AmdiJobBacklog
1. Scale workers: `kubectl scale deploy/amdi-worker --replicas=10`.
2. Inspect worker queue depth: `arq inspect amdi-ingest`.
