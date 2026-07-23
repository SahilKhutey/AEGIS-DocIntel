'''
AEGIS-DocIntel / AMDI-OS — Advanced Features REST API Router
=============================================================
Exposes endpoints for:
  - PII & Compliance Redaction Pre-Filter
  - Cross-Document Entity Resolution
  - Document Version & Structural Diff Engine
  - Ingestion Anomaly & Adversarial Gate
  - Matrix Engine Quantity & Currency Normalization
  - Query Decomposition Pre-Processor
  - Topological Percolation Resilience Analysis
  - Ising-Model Simulated Annealing Optimization
'''
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.compliance.redaction_engine import detect_pii, apply_redaction_policy, RedactionPolicy
from src.entity.canonicalizer import extract_mentions, score_mention_pairs, cluster_into_canonical_entities
from src.versioning.diff_engine import compute_structural_diff, query_changes_since
from src.ingestion.anomaly_gate import run_ingestion_gate
from src.engines.matrix.unit_normalizer import parse_quantity, normalize_currency
from src.query.decomposer import build_query_dag, execute_query_dag
from src.engines.topology.topology_engine import TopologyEngine
from src.engines.optimization.optimization_engine import OptimizationEngine

router = APIRouter(prefix="/v1/advanced", tags=["Advanced Systems & Pre-LLM"])


# ============================================================
# PII & COMPLIANCE REDACTION
# ============================================================

class PIIScanRequest(BaseModel):
    element_id: str = "elem_01"
    text: str
    redact_ssn: bool = True
    redact_credit_card: bool = True


@router.post("/compliance/pii-scan")
async def scan_and_redact_pii(req: PIIScanRequest) -> Dict[str, Any]:
    elem = {"id": req.element_id, "text": req.text}
    entities = detect_pii(elem)

    policies = []
    if req.redact_ssn:
        policies.append(RedactionPolicy("US_SSN", "redact"))
    if req.redact_credit_card:
        policies.append(RedactionPolicy("CREDIT_CARD", "redact"))

    redacted_elem, report = apply_redaction_policy(elem, entities, policies)
    return {
        "redacted_text": redacted_elem["text"],
        "entities_found": [e.__dict__ for e in entities],
        "redactions_applied": report.redactions_applied,
    }


# ============================================================
# CROSS-DOCUMENT ENTITY RESOLUTION
# ============================================================

class EntityResolveRequest(BaseModel):
    documents: List[Dict[str, Any]]


@router.post("/entity/resolve")
async def resolve_entities(req: EntityResolveRequest) -> Dict[str, Any]:
    mentions = extract_mentions(req.documents)
    scores = score_mention_pairs(mentions)
    canonicals = cluster_into_canonical_entities(mentions, scores, threshold=0.8)
    return {
        "total_mentions": len(mentions),
        "canonical_entities": [
            {
                "canonical_id": c.canonical_id,
                "canonical_name": c.canonical_name,
                "mention_count": len(c.mentions),
            }
            for c in canonicals
        ],
    }


# ============================================================
# DOCUMENT VERSION & STRUCTURAL DIFF
# ============================================================

class DiffRequest(BaseModel):
    v1_document: Dict[str, Any]
    v2_document: Dict[str, Any]


@router.post("/versioning/diff")
async def diff_document_versions(req: DiffRequest) -> Dict[str, Any]:
    diff = compute_structural_diff(req.v1_document, req.v2_document)
    return {
        "from_version": diff.from_version,
        "to_version": diff.to_version,
        "edit_distance": diff.edit_distance,
        "edits": [e.__dict__ for e in diff.edits],
    }


# ============================================================
# INGESTION ANOMALY & ADVERSARIAL GATE
# ============================================================

class AnomalyScanRequest(BaseModel):
    document: Dict[str, Any]


@router.post("/ingestion/anomaly-check")
async def scan_ingestion_anomalies(req: AnomalyScanRequest) -> Dict[str, Any]:
    res = run_ingestion_gate(req.document)
    return {
        "document_id": res.document_id,
        "action": res.action,
        "flags": [f.__dict__ for f in res.flags],
    }


# ============================================================
# MATRIX UNIT & CURRENCY NORMALIZATION
# ============================================================

class QuantityNormalizeRequest(BaseModel):
    cell_text: str
    target_currency: str = "USD"
    exchange_rate: float = 1.0


@router.post("/matrix/normalize-quantity")
async def normalize_cell_quantity(req: QuantityNormalizeRequest) -> Dict[str, Any]:
    parsed = parse_quantity(req.cell_text)
    if parsed is None:
        raise HTTPException(status_code=400, detail="Could not parse quantity from cell text")

    if parsed.quantity_type == "currency":
        norm = normalize_currency(parsed, target_currency=req.target_currency, exchange_rate=req.exchange_rate)
        return norm.__dict__

    return parsed.__dict__


# ============================================================
# QUERY DECOMPOSITION PRE-PROCESSOR
# ============================================================

class QueryDecomposeRequest(BaseModel):
    query: str


@router.post("/query/decompose")
async def decompose_query(req: QueryDecomposeRequest) -> Dict[str, Any]:
    dag = build_query_dag(req.query)
    return {
        "original_query": dag.original_query,
        "combination_step": dag.combination_step,
        "sub_queries": [sq.__dict__ for sq in dag.sub_queries],
    }


# ============================================================
# TOPOLOGICAL PERCOLATION RESILIENCE
# ============================================================

@router.get("/topology/percolation-check")
async def estimate_resilience() -> Dict[str, Any]:
    import networkx as nx
    G = nx.grid_2d_graph(4, 4)
    topo = TopologyEngine()
    res = topo.estimate_percolation_threshold(G, num_trials=20)
    return {
        "percolation_threshold": res["threshold"],
        "critical_nodes": [str(n) for n in res["critical_nodes"]],
    }


# ============================================================
# ISING-MODEL ANNEALING SOLVER
# ============================================================

class IsingAnnealRequest(BaseModel):
    dimension: int = 4


@router.post("/optimization/ising-anneal")
async def anneal_master_objective(req: IsingAnnealRequest) -> Dict[str, Any]:
    import numpy as np
    d = max(2, min(10, req.dimension))
    interactions = np.eye(d) * 0.1
    priors = np.ones(d)
    opt = OptimizationEngine()
    res = opt.anneal_master_objective(interactions, priors, num_sweeps=50)
    return {
        "energy": res["energy"],
        "weights": list(res["weights"]),
    }


# ============================================================
# MASTER UNIFIED MATHEMATICAL EVALUATION (ALL 16 DOMAINS)
# ============================================================

class UnifiedMathRequest(BaseModel):
    document: Dict[str, Any]


@router.post("/math/unified-evaluation")
async def evaluate_unified_math(req: UnifiedMathRequest) -> Dict[str, Any]:
    from src.math_concepts.master_math_engine import MasterUnifiedMathEngine
    engine = MasterUnifiedMathEngine()
    res = engine.evaluate_document_state(req.document)
    return res.__dict__


# ============================================================
# SPEECH & IMAGE LAYOUT PARSING ENDPOINTS
# ============================================================

class SpeechParseRequest(BaseModel):
    filename: str = "audio_sample.wav"
    audio_base64: Optional[str] = None


@router.post("/ingestion/parse-speech")
async def parse_speech_audio(req: SpeechParseRequest) -> Dict[str, Any]:
    import base64
    from src.ingestion.speech_loader import SpeechLoader

    loader = SpeechLoader()
    raw_bytes = base64.b64decode(req.audio_base64) if req.audio_base64 else b"RIFF____WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data____"
    doc_obj = await loader.load(raw_bytes, filename=req.filename)
    return {
        "filename": doc_obj.filename,
        "format": doc_obj.format.value,
        "page_count": doc_obj.page_count,
        "word_count": doc_obj.word_count,
        "transcript": doc_obj.text_content,
        "metadata": doc_obj.metadata,
    }


class ImageLayoutParseRequest(BaseModel):
    filename: str = "document_page.png"
    blur_threshold: float = 100.0


@router.post("/ingestion/parse-image-layout")
async def parse_image_layout(req: ImageLayoutParseRequest) -> Dict[str, Any]:
    import io
    from PIL import Image, ImageDraw
    from src.ingestion.image_parser import AdvancedImageParser

    # Generate test page image
    img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 760, 100], fill=(230, 230, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    parser = AdvancedImageParser(blur_threshold=req.blur_threshold)
    analysis = parser.parse_image(buf.getvalue())
    return analysis.to_dict()


# ============================================================
# LLM TOKEN-OPTIMIZED EXPORT ENDPOINT
# ============================================================

class LLMExportRequest(BaseModel):
    system_prompt: Optional[str] = "You are a financial analysis AI assistant."
    context_text: str
    summary_text: Optional[str] = None
    max_tokens: int = 4000
    format_type: str = "markdown"  # 'markdown' | 'json'
    compact_keys: bool = True


@router.post("/export/llm-optimized")
async def export_llm_optimized(req: LLMExportRequest) -> Dict[str, Any]:
    from src.export.universal_exporter import UniversalExportObject
    from src.export.llm_optimized_exporter import LLMTokenOptimizedExporter, LLMExportConfig
    from src.ael.token_budget import count_tokens

    ueo = UniversalExportObject(
        system=req.system_prompt or "",
        context=req.context_text,
        summary=req.summary_text or "",
        citations=[{"doc_id": "Doc1", "page": 1}],
        metadata={"export_type": "llm_optimized"},
    )

    cfg = LLMExportConfig(
        max_tokens=req.max_tokens,
        format_type=req.format_type,
        compact_keys=req.compact_keys,
    )
    exporter = LLMTokenOptimizedExporter(config=cfg)
    output_content = exporter.export(ueo)
    tokens_used = count_tokens(output_content)

    return {
        "format_type": req.format_type,
        "max_tokens_budget": req.max_tokens,
        "tokens_used": tokens_used,
        "compression_ratio": round(tokens_used / max(1, count_tokens(req.context_text)), 4),
        "exported_content": output_content,
    }
