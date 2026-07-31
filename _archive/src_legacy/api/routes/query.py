'''
AMDI-OS — FastAPI APIRouter Endpoints
======================================
Implements /ingest, /query, /query/stream, /documents, and AEL export features.
'''
from __future__ import annotations

import logging
import time
import uuid
from typing import List, Dict, Any, Optional

try:
    from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

import numpy as np

from src.core.document_object import DocumentObject
from src.engines.geometry.element import ElementType, GeometricElement
from src.ael.exporter import AgentExporter
from src.core.config import settings

log = logging.getLogger('amdi.api.routes')

if HAS_FASTAPI:
    router = APIRouter()
    _requests_total = 0
    _queries_total = 0

    # ─────────────────────────────────────────────────────────────
    # Schemas
    # ─────────────────────────────────────────────────────────────

    class IngestResponse(BaseModel):
        doc_id:             str
        filename:           str
        pages:              int
        elements:           int
        tables:             int
        templates:          int
        ingestion_ms:       float
        compression_pct:    float
        status:             str = 'ok'

    class QueryRequest(BaseModel):
        question: str = Field(..., min_length=1, max_length=2000)
        doc_id:   Optional[str] = None
        top_k:    int = Field(default=12, ge=1, le=50)
        stream:   bool = False
        # Agent Export Layer parameters
        export_agent: Optional[str] = None
        export_format: Optional[str] = 'json'
        api_key: Optional[str] = None
        model: Optional[str] = None

    class QueryResponse(BaseModel):
        question:      str
        answer:        str
        citations:     list[dict] = []
        confidence:    float
        confidence_label: str
        query_type:    str
        weights_used:  dict[str, float]
        table_direct:  list[str] = []
        grounded:      bool
        latency_ms:    float
        tokens_used:   int
        model:         str

    class DocumentMeta(BaseModel):
        doc_id:    str
        filename:  str
        pages:     int
        tables:    int
        ingested_at: float

    # ─────────────────────────────────────────────────────────────
    # Routes
    # ─────────────────────────────────────────────────────────────



    @router.delete('/document', status_code=status.HTTP_204_NO_CONTENT)
    async def clear_document(request: Request):
        global _requests_total
        _requests_total += 1
        doc_registry = request.app.state.doc_registry
        orchestrator = request.app.state.orchestrator
        doc_registry.clear()
        if orchestrator:
            orchestrator._elements.clear()
            orchestrator._tables.clear()
            orchestrator._templates.clear()
            orchestrator._graph = None
            orchestrator._hypergraph = None
            if hasattr(orchestrator, 'physics') and orchestrator.physics:
                orchestrator.physics.particles.clear()

    @router.get('/documents/{doc_id}/elements')
    async def get_elements(doc_id: str, request: Request):
        global _requests_total
        _requests_total += 1
        orchestrator = request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')
        elements = orchestrator.get_document_elements(doc_id)
        return [
            {
                'element_id': e.element_id,
                'doc_id': e.doc_id,
                'page': e.page,
                'type': e.type.value,
                'content': e.content,
                'bbox': e.bbox.to_tuple() if e.bbox else None,
                'importance_weight': getattr(e, 'importance_weight', 1.0),
                'section': e.section
            }
            for e in elements
        ]

    @router.post('/ingest', response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
    async def ingest(request: Request, file: UploadFile = File(...)):
        global _requests_total
        _requests_total += 1
        orchestrator = request.app.state.orchestrator
        doc_registry = request.app.state.doc_registry

        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')
        raw = await file.read()
        if not raw:
            raise HTTPException(400, 'Empty file')

        doc = DocumentObject(
            doc_id=str(uuid.uuid4()),
            filename=file.filename or 'upload',
            raw_bytes=raw,
        )

        t0 = time.perf_counter()
        try:
            stats = await orchestrator.ingest(doc)
        except Exception as e:
            log.error('Ingest failed: %s', e, exc_info=True)
            raise HTTPException(500, f'Ingest failed: {e}')

        elapsed_ms = (time.perf_counter() - t0) * 1000
        stats['ingestion_ms'] = round(elapsed_ms, 1)

        doc_registry[stats['doc_id']] = {
            'doc_id':      stats['doc_id'],
            'filename':    stats.get('filename', file.filename),
            'pages':       stats.get('pages', 0),
            'tables':      stats.get('tables', 0),
            'ingested_at': time.time(),
        }

        return IngestResponse(
            doc_id          = stats['doc_id'],
            filename        = stats.get('filename', file.filename),
            pages           = stats.get('pages', 0),
            elements        = stats.get('elements', 0),
            tables          = stats.get('tables', 0),
            templates       = stats.get('templates', 0),
            ingestion_ms    = round(elapsed_ms, 1),
            compression_pct = stats.get('compression_pct', 0.0),
        )

    @router.post('/query', response_model=QueryResponse)
    async def query(req: QueryRequest, request: Request):
        global _requests_total, _queries_total
        _requests_total += 1
        _queries_total += 1
        orchestrator = request.app.state.orchestrator
        doc_registry = request.app.state.doc_registry

        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')

        t0 = time.perf_counter()

        # If export_agent is specified, route through Agent Export Layer
        if req.export_agent:
            try:
                # 1. Resolve doc_id
                doc_id = req.doc_id
                if not doc_id:
                    if doc_registry:
                        doc_id = max(doc_registry.values(), key=lambda d: d.get('ingested_at', 0)).get('doc_id')
                    else:
                        raise HTTPException(400, 'No doc_id specified and no documents ingested.')

                doc_meta = doc_registry.get(doc_id)
                if not doc_meta:
                    doc_meta = {
                        'doc_id': doc_id,
                        'filename': 'document.pdf',
                        'pages': 1,
                        'language': 'English',
                        'document_type': 'Unknown'
                    }

                # 2. Extract context elements
                elements = orchestrator.get_document_elements(doc_id)
                tables_elems = orchestrator.get_document_tables(doc_id)

                # Convert TableMatrix into dict format for UEO
                tables = []
                if orchestrator._matrix is not None:
                    for e in tables_elems:
                        tbl_matrix = orchestrator._matrix.get(e.element_id)
                        if tbl_matrix:
                            computed = {}
                            for h in tbl_matrix.headers:
                                s = tbl_matrix.sum(h)
                                a = tbl_matrix.avg(h)
                                g = tbl_matrix.growth(h)
                                if s is not None and not np.isnan(s):
                                    computed[f'sum_{h}'] = s
                                if a is not None and not np.isnan(a):
                                    computed[f'avg_{h}'] = a
                                if g is not None and not np.isnan(g):
                                    computed[f'growth_{h}'] = g
                            
                            tables.append({
                                'name': f'Table_{tbl_matrix.matrix_id}' if tbl_matrix.matrix_id else 'Table',
                                'page': tbl_matrix.page,
                                'headers': tbl_matrix.headers,
                                'data': tbl_matrix.raw_rows,
                                'computed_metrics': computed,
                                'element_id': tbl_matrix.element_id
                            })

                # Graph relationships
                graph = orchestrator.get_document_graph()
                relationships = []
                if graph is not None and hasattr(graph, 'graph'):
                    nx_g = graph.graph
                    if hasattr(nx_g, 'edges'):
                        for u, v, attrs in nx_g.edges(data=True):
                            relationships.append({
                                'id': f'{u}->{v}',
                                'src': u,
                                'dst': v,
                                'type': attrs.get('type', 'related') if attrs else 'related',
                                'weight': attrs.get('weight', 1.0) if attrs else 1.0
                            })

                # Templates
                templates_objs = orchestrator.get_document_templates(doc_id)
                templates = [tmpl.to_dict() if hasattr(tmpl, 'to_dict') else tmpl for tmpl in templates_objs]

                # Run retriever to find query-relevant elements
                retrieved = await orchestrator._call_maybe_async(
                    orchestrator._retriever.retrieve,
                    query=req.question,
                    elements=elements,
                    tables=tables_elems,
                    graph=graph,
                    hypergraph=orchestrator._hypergraph,
                    top_k=req.top_k
                )
                citations_list = [r.element for r in retrieved.results] if retrieved else []

                # Compile summary fields
                all_keyphrases = []
                for e in elements:
                    if hasattr(e, 'keyphrases') and e.keyphrases:
                        all_keyphrases.extend(e.keyphrases)
                from collections import Counter
                keyphrase_counts = Counter(all_keyphrases)
                top_keyphrases = [kp for kp, count in keyphrase_counts.most_common(15)]

                all_entities = []
                for e in elements:
                    if hasattr(e, 'entities') and e.entities:
                        all_entities.extend(e.entities)
                unique_entities = []
                seen_entities = set()
                for ent in all_entities:
                    if isinstance(ent, dict):
                        ent_type = ent.get("type")
                        ent_val = ent.get("value") or ent.get("text") or ""
                    elif isinstance(ent, tuple) and len(ent) >= 2:
                        ent_type = ent[0]
                        ent_val = ent[1]
                    else:
                        ent_type = getattr(ent, "type", None)
                        ent_val = getattr(ent, "value", None) or getattr(ent, "text", None) or ""
                    
                    if not ent_type or not ent_val:
                        continue
                    
                    k = f'{ent_type}:{ent_val.lower()}'
                    if k not in seen_entities:
                        seen_entities.add(k)
                        unique_entities.append({
                            "type": ent_type,
                            "value": ent_val,
                            "text": ent_val
                        })

                sections = []
                headings = [e for e in elements if e.type == ElementType.HEADING]
                for h in headings:
                    sections.append({
                        'name': h.content,
                        'page': h.page,
                        'level': getattr(h, 'level', 1)
                    })

                # Create UEO package
                exporter = AgentExporter()
                ueo = exporter.create_ueo(
                    query=req.question,
                    doc_metadata={
                        'doc_id': doc_id,
                        'document_name': doc_meta.get('filename', 'document.pdf'),
                        'pages': doc_meta.get('pages', 1),
                        'language': doc_meta.get('language', 'English'),
                        'document_type': doc_meta.get('document_type', 'Research Paper')
                    },
                    summary={
                        'title': doc_meta.get('filename', 'document.pdf'),
                        'abstract': ' '.join([e.content for e in elements if e.type == ElementType.TEXT][:3]),
                        'key_topics': top_keyphrases[:5],
                        'keywords': top_keyphrases[5:15],
                        'entities': unique_entities[:20],
                        'sections': sections
                    },
                    elements=elements,
                    tables=tables,
                    relationships=relationships,
                    templates=templates,
                    citations_list=citations_list,
                    confidence_scores={
                        'overall': 0.95,
                        'semantic': 0.9,
                        'numerical': 0.9,
                        'structural': 0.9,
                        'retrieval': 0.9
                    }
                )

                # 3. Resolve API keys for external agent
                api_key = req.api_key
                if not api_key:
                    agent_lower = req.export_agent.lower()
                    if agent_lower == 'chatgpt':
                        api_key = settings.openai_api_key or settings.llm_api_key
                    elif agent_lower == 'gemini':
                        api_key = settings.google_api_key or settings.llm_api_key
                    elif agent_lower == 'claude':
                        api_key = settings.anthropic_api_key or settings.llm_api_key
                    elif agent_lower == 'deepseek':
                        api_key = settings.llm_api_key
                    elif agent_lower == 'qwen':
                        api_key = settings.llm_api_key
                    else:
                        api_key = 'EMPTY'

                # 4. Call Agent
                result = await exporter.export_and_verify(
                    ueo=ueo,
                    agent=req.export_agent,
                    api_key=api_key or 'EMPTY',
                    model=req.model,
                    temperature=0.1
                )

                elapsed_ms = (time.perf_counter() - t0) * 1000
                verification = result.get('verification', {})
                calibrated_conf = verification.get('calibrated_confidence', 0.5)

                weights_val = getattr(retrieved, 'weights', {}) if retrieved else {}
                if hasattr(weights_val, 'to_dict'):
                    weights_used_dict = weights_val.to_dict()
                else:
                    weights_used_dict = weights_val if isinstance(weights_val, dict) else {}

                return QueryResponse(
                    question=req.question,
                    answer=result.get('answer', ''),
                    citations=[
                        {
                            'page': c.get('page'),
                            'section': c.get('section'),
                            'is_valid': c.get('is_valid'),
                            'reason': c.get('reason')
                        }
                        for c in verification.get('verified_citations', [])
                    ],
                    confidence=calibrated_conf,
                    confidence_label='HIGH' if calibrated_conf >= 0.85 else 'MEDIUM' if calibrated_conf >= 0.5 else 'LOW',
                    query_type=getattr(retrieved, 'query_type', 'semantic') if retrieved else 'semantic',
                    weights_used=weights_used_dict,
                    table_direct=getattr(retrieved, 'table_answers', []) if retrieved else [],
                    grounded=verification.get('is_grounded', False),
                    latency_ms=round(elapsed_ms, 1),
                    tokens_used=result.get('input_tokens', 0) + result.get('output_tokens', 0),
                    model=result.get('model', 'mock')
                )
            except Exception as e:
                log.error('AEL Query failed: %s', e, exc_info=True)
                raise HTTPException(500, f'AEL query failed: {e}')

        # Default local engine path if not exporting
        try:
            result = await orchestrator.query(req.question, doc_id=req.doc_id, top_k=req.top_k)
        except Exception as e:
            log.error('Query failed: %s', e, exc_info=True)
            raise HTTPException(500, f'Query failed: {e}')

        elapsed_ms = (time.perf_counter() - t0) * 1000

        return QueryResponse(
            question         = req.question,
            answer           = result.get('answer', ''),
            citations        = result.get('citations', []),
            confidence       = result.get('confidence', 0.5),
            confidence_label = result.get('confidence_label', 'MEDIUM'),
            query_type       = result.get('query_type', 'semantic'),
            weights_used     = result.get('weights_used', {}),
            table_direct     = result.get('table_direct', []),
            grounded         = result.get('grounded', False),
            latency_ms       = round(elapsed_ms, 1),
            tokens_used      = result.get('tokens_used', 0),
            model            = result.get('model', 'mock'),
        )

    @router.get('/query/stream')
    async def query_stream(question: str, request: Request, doc_id: Optional[str] = None):
        orchestrator = request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')

        async def event_generator():
            try:
                async for token in orchestrator.stream_query(question):
                    yield f'data: {token}\n\n'
                yield 'data: [DONE]\n\n'
            except Exception as e:
                yield f'data: [ERROR] {e}\n\n'

        return StreamingResponse(event_generator(), media_type='text/event-stream')

    @router.get('/documents', response_model=list[DocumentMeta])
    async def list_documents(request: Request):
        doc_registry = request.app.state.doc_registry
        return [DocumentMeta(**v) for v in doc_registry.values()]

    @router.delete('/documents/{doc_id}', status_code=status.HTTP_204_NO_CONTENT)
    async def delete_document(doc_id: str, request: Request):
        doc_registry = request.app.state.doc_registry
        orchestrator = request.app.state.orchestrator

        if doc_id not in doc_registry:
            raise HTTPException(404, f'Document {doc_id} not found')
        del doc_registry[doc_id]
        if orchestrator:
            await orchestrator.memory.invalidate(doc_id)

    @router.get('/documents/{doc_id}/explain')
    async def explain(doc_id: str, question: str, request: Request):
        orchestrator = request.app.state.orchestrator
        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')
        try:
            from src.engines.fusion.adaptive_fusion import AdaptiveFusionEngine
            afe = AdaptiveFusionEngine()
            return {'explanation': afe.explain_routing(question)}
        except Exception as e:
            raise HTTPException(500, str(e))

    @router.get('/documents/{doc_id}/export')
    async def export_document(
        doc_id: str,
        request: Request,
        format: str = 'json'
    ):
        '''
        Compiles and downloads the Universal Export Object (UEO) for a document.
        '''
        orchestrator = request.app.state.orchestrator
        doc_registry = request.app.state.doc_registry

        if not orchestrator:
            raise HTTPException(503, 'Orchestrator not initialized')

        doc_meta = doc_registry.get(doc_id)
        if not doc_meta:
            raise HTTPException(404, f'Document {doc_id} not found')

        # Extract elements
        elements = orchestrator.get_document_elements(doc_id)
        tables_elems = orchestrator.get_document_tables(doc_id)

        # Convert tables
        tables = []
        if orchestrator._matrix is not None:
            for e in tables_elems:
                tbl_matrix = orchestrator._matrix.get(e.element_id)
                if tbl_matrix:
                    computed = {}
                    for h in tbl_matrix.headers:
                        s = tbl_matrix.sum(h)
                        a = tbl_matrix.avg(h)
                        g = tbl_matrix.growth(h)
                        if s is not None and not np.isnan(s):
                            computed[f'sum_{h}'] = s
                        if a is not None and not np.isnan(a):
                            computed[f'avg_{h}'] = a
                        if g is not None and not np.isnan(g):
                            computed[f'growth_{h}'] = g
                    
                    tables.append({
                        'name': f'Table_{tbl_matrix.matrix_id}' if tbl_matrix.matrix_id else 'Table',
                        'page': tbl_matrix.page,
                        'headers': tbl_matrix.headers,
                        'data': tbl_matrix.raw_rows,
                        'computed_metrics': computed,
                        'element_id': tbl_matrix.element_id
                    })

        # Relationships
        graph = orchestrator.get_document_graph()
        relationships = []
        if graph is not None and hasattr(graph, 'graph'):
            nx_g = graph.graph
            if hasattr(nx_g, 'edges'):
                for u, v, attrs in nx_g.edges(data=True):
                    relationships.append({
                        'id': f'{u}->{v}',
                        'src': u,
                        'dst': v,
                        'type': attrs.get('type', 'related') if attrs else 'related',
                        'weight': attrs.get('weight', 1.0) if attrs else 1.0
                    })

        # Templates
        templates_objs = orchestrator.get_document_templates(doc_id)
        templates = [tmpl.to_dict() if hasattr(tmpl, 'to_dict') else tmpl for tmpl in templates_objs]

        # Compile summaries
        all_keyphrases = []
        for e in elements:
            if hasattr(e, 'keyphrases') and e.keyphrases:
                all_keyphrases.extend(e.keyphrases)
        from collections import Counter
        keyphrase_counts = Counter(all_keyphrases)
        top_keyphrases = [kp for kp, count in keyphrase_counts.most_common(15)]

        all_entities = []
        for e in elements:
            if hasattr(e, 'entities') and e.entities:
                all_entities.extend(e.entities)
        unique_entities = []
        seen_entities = set()
        for ent in all_entities:
            if isinstance(ent, dict):
                ent_type = ent.get("type")
                ent_val = ent.get("value") or ent.get("text") or ""
            elif isinstance(ent, tuple) and len(ent) >= 2:
                ent_type = ent[0]
                ent_val = ent[1]
            else:
                ent_type = getattr(ent, "type", None)
                ent_val = getattr(ent, "value", None) or getattr(ent, "text", None) or ""
            
            if not ent_type or not ent_val:
                continue
            
            k = f'{ent_type}:{ent_val.lower()}'
            if k not in seen_entities:
                seen_entities.add(k)
                unique_entities.append({
                    "type": ent_type,
                    "value": ent_val,
                    "text": ent_val
                })

        sections = []
        headings = [e for e in elements if e.type == ElementType.HEADING]
        for h in headings:
            sections.append({
                'name': h.content,
                'page': h.page,
                'level': getattr(h, 'level', 1)
            })

        exporter = AgentExporter()
        ueo = exporter.create_ueo(
            query='Document export',
            doc_metadata={
                'doc_id': doc_id,
                'document_name': doc_meta.get('filename', 'document.pdf'),
                'pages': doc_meta.get('pages', 1),
                'language': doc_meta.get('language', 'English'),
                'document_type': doc_meta.get('document_type', 'Research Paper')
            },
            summary={
                'title': doc_meta.get('filename', 'document.pdf'),
                'abstract': ' '.join([e.content for e in elements if e.type == ElementType.TEXT][:3]),
                'key_topics': top_keyphrases[:5],
                'keywords': top_keyphrases[5:15],
                'entities': unique_entities[:20],
                'sections': sections
            },
            elements=elements,
            tables=tables,
            relationships=relationships,
            templates=templates,
            citations_list=[],
            confidence_scores={
                'overall': 0.95,
                'semantic': 0.9,
                'numerical': 0.9,
                'structural': 0.9,
                'retrieval': 0.9
            }
        )

        format_lower = format.lower()
        if format_lower == 'markdown':
            from src.ael.formats.markdown_exporter import MarkdownExporter
            return MarkdownExporter.export(ueo)
        elif format_lower == 'yaml':
            from src.ael.formats.yaml_exporter import YAMLExporter
            return YAMLExporter.export(ueo)
        else:
            return ueo.to_dict()
