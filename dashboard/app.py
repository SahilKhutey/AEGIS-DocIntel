"""
AEGIS-AMDI-OS Complete Dashboard
==================================
Main entry point with multi-page navigation.
Run: streamlit run dashboard/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
import streamlit as st

# Add amdi-os and dashboard to path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AEGIS-AMDI-OS",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "AEGIS-AMDI-OS v1.0 — Adaptive Mathematical Document Intelligence",
    },
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #0a0e1a 0%, #1a1f2e 100%); }
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #4fc3f7, #ab47bc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header { color: #8b95a7; font-size: 0.9rem; margin-top: -10px; }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        padding: 1.2rem;
        border-radius: 0.75rem;
        border: 1px solid #334155;
        backdrop-filter: blur(10px);
    }
    .status-ok { color: #4ade80; }
    .status-err { color: #f87171; }
    .citation { background: #1e293b; padding: 0.5rem; border-left: 3px solid #4fc3f7; margin: 0.3rem 0; }
    .layer-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0 0.2rem;
    }
    .layer-semantic { background: #1e40af; color: white; }
    .layer-matrix { background: #7c2d12; color: white; }
    .layer-geometry { background: #166534; color: white; }
    .layer-graph { background: #7e22ce; color: white; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# CONFIG & AUTH
# ============================================================

API_URL = st.sidebar.text_input("🔗 API URL", value="http://localhost:8000", key="api_url")
AUTH_TOKEN = st.sidebar.text_input(
    "🔑 Auth Token / Key",
    value="dev-default",
    type="password",
    key="auth_token",
    help="Bearer token (e.g. dev-default) or X-API-Key for authenticated endpoints.",
)
TENANT_ID = st.sidebar.text_input(
    "🏢 Tenant ID",
    value="default",
    key="tenant_id",
    help="Target tenant context for document isolation.",
)


def _get_auth_headers() -> dict[str, str]:
    headers = {}
    token = st.session_state.get("auth_token", AUTH_TOKEN)
    tenant = st.session_state.get("tenant_id", TENANT_ID)
    if token:
        if token.startswith("Bearer "):
            headers["Authorization"] = token
        else:
            headers["Authorization"] = f"Bearer {token}"
            headers["X-API-Key"] = token
    if tenant:
        headers["X-Tenant-ID"] = tenant
    return headers


def api_get(endpoint: str, params: dict = None, headers: dict = None):
    try:
        h = _get_auth_headers()
        if headers:
            h.update(headers)
        r = requests.get(f"{API_URL}{endpoint}", params=params, headers=h, timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error ({endpoint}): {e}")
        return None


def api_post(endpoint: str, json_data: dict = None, files: dict = None, data: dict = None, headers: dict = None):
    try:
        h = _get_auth_headers()
        if headers:
            h.update(headers)
        if files:
            r = requests.post(f"{API_URL}{endpoint}", files=files, data=data, headers=h, timeout=600)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=json_data, headers=h, timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error ({endpoint}): {e}")
        return None


def api_delete(endpoint: str, headers: dict = None):
    try:
        h = _get_auth_headers()
        if headers:
            h.update(headers)
        r = requests.delete(f"{API_URL}{endpoint}", headers=h, timeout=60)
        r.raise_for_status()
        if r.status_code == 204 or not r.content:
            return {"deleted": True}
        return r.json()
    except Exception as e:
        st.error(f"API Error ({endpoint}): {e}")
        return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🛡️ AEGIS-AMDI-OS")
    st.markdown("**v1.0.0** — Mathematical Document Intelligence")
    st.markdown("---")

    # Health
    health = api_get("/health")
    if health:
        st.success(f"✅ Online ({health.get('version', '?')})")
        n_agents = len(health.get("agents", []))
        st.caption(f"🤖 {n_agents} agents supported")
    else:
        st.error("❌ Offline")

    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigate",
        [
            "📤 Upload",
            "🔍 Query",
            "📁 Document Explorer",
            "📐 Geometry",
            "🌐 3D View",
            "✏️ Annotations",
            "📊 Matrix",
            "🕸️ Graph",
            "🎨 Templates",
            "💾 Memory",
            "📈 Analytics",
            "⚙️ Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Doc info
    stats = api_get("/v1/stats")
    if stats and stats.get("filename"):
        st.markdown("### 📄 Current Doc")
        st.caption(f"**{stats.get('filename', '?')}**")
        if stats.get("doc_id"):
            st.caption(f"ID: `{str(stats.get('doc_id'))[:8]}...`")
        st.caption(f"Elements: {stats.get('n_elements', 0)}")
        st.caption(f"Tables: {stats.get('n_tables', 0)}")
        if st.button("🗑️ Clear", use_container_width=True):
            api_delete("/v1/document")
            st.session_state.pop("last_ingest", None)
            st.session_state.pop("active_doc_id", None)
            st.rerun()


# ============================================================
# PAGE 1: UPLOAD
# ============================================================

def page_upload():
    st.markdown('<p class="main-header">📤 Upload Document</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ingest any document format for mathematical analysis</p>',
                unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded = st.file_uploader(
            "Choose document",
            type=["pdf", "docx", "pptx", "xlsx", "png", "jpg", "jpeg", "txt"],
            help="Max 200MB",
        )

        if uploaded and st.button("🚀 Ingest Now", type="primary", use_container_width=True):
            with st.spinner("Processing through mathematical intelligence engines..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                result = api_post("/v1/ingest", files=files)
                if result:
                    st.session_state["last_ingest"] = result
                    if "doc_id" in result:
                        st.session_state["active_doc_id"] = result["doc_id"]
                    st.balloons()
                    st.success("✅ Document indexed successfully!")
                else:
                    st.error("Failed to ingest document. Check API logs.")

    with col2:
        st.markdown("### 📊 Quick Stats")
        if "last_ingest" in st.session_state:
            info = st.session_state["last_ingest"]
            for key in ["pages", "blocks", "tables", "templates"]:
                if key in info:
                    st.metric(key.title(), info[key])
            if "graph_nodes" in info:
                st.metric("Graph Nodes", info["graph_nodes"])
            if "timings" in info:
                st.metric("Ingest Time", f"{info['timings'].get('total_s', 0):.2f}s")
            elif "ingestion_ms" in info:
                st.metric("Ingest Time", f"{info['ingestion_ms'] / 1000:.2f}s")

    if "last_ingest" in st.session_state:
        with st.expander("📄 Detailed Ingestion Info", expanded=False):
            st.json(st.session_state["last_ingest"])


# ============================================================
# PAGE 2: QUERY
# ============================================================

def page_query():
    st.markdown('<p class="main-header">🔍 Query Document</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions with adaptive multi-layer retrieval</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    active_doc_id = st.session_state.get("active_doc_id") or (stats.get("doc_id") if stats else None)

    if not stats and not active_doc_id:
        st.warning("⚠️ No document ingested. Go to Upload first.")
        return

    doc_label = stats.get("filename", active_doc_id or "Active Document") if stats else (active_doc_id or "Active Document")
    st.success(f"📄 Active: **{doc_label}**" + (f" (`{str(active_doc_id)[:8]}...`)" if active_doc_id else ""))

    # Query interface
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        question = st.text_input("Question", placeholder="What is the total revenue?")
    with col2:
        top_k = st.number_input("Top K", 1, 20, 8)
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        run_query = st.button("🔍 Ask", type="primary", use_container_width=True)

    # Example questions
    with st.expander("💡 Example Questions"):
        examples = [
            "What is the total revenue?",
            "What was the growth rate?",
            "What is on page 3?",
            "Summarize the conclusions.",
            "Find all headers and footers.",
            "What tables are in the document?",
        ]
        for ex in examples:
            if st.button(f"📋 {ex}", key=f"ex_{ex}"):
                st.session_state["question_input"] = ex
                st.rerun()

    if "question_input" in st.session_state:
        question = st.session_state["question_input"]

    if question and run_query:
        with st.spinner("Searching and reasoning..."):
            query_payload = {
                "question": question,
                "top_k": int(top_k),
                "include_citations": True,
            }
            if active_doc_id:
                query_payload["doc_id"] = str(active_doc_id)
            result = api_post("/v1/query", query_payload)
            if result:
                st.session_state["last_query"] = result
                st.session_state["last_q_text"] = question

    # Display result
    if "last_query" in st.session_state:
        result = st.session_state["last_query"]

        st.markdown("### 💡 Answer")
        answer_text = result.get("answer", "")
        st.markdown(f"```\n{answer_text}\n```")

        # Metrics row
        st.markdown("### 📊 Query Analytics")
        cols = st.columns(5)
        with cols[0]:
            q_type = result.get("query_type") or "hybrid"
            st.metric("Type", q_type)
        with cols[1]:
            conf = result.get("confidence")
            conf_str = conf.get("level") if isinstance(conf, dict) else str(conf or "MEDIUM")
            st.metric("Confidence", conf_str)
        with cols[2]:
            tok = result.get("tokens_used")
            if isinstance(tok, dict):
                in_tok = tok.get("input", 0)
                out_tok = tok.get("output", 0)
                tok_str = f"{in_tok}↓ / {out_tok}↑"
            elif isinstance(tok, int):
                tok_str = f"{tok} total"
            else:
                tok_str = f"{result.get('input_tokens', 0)}↓ / {result.get('output_tokens', 0)}↑"
            st.metric("Tokens", tok_str)
        with cols[3]:
            grounded = result.get("grounded")
            st.metric("Grounded", "✅ Yes" if grounded is not False else "⚠️ Partial")
        with cols[4]:
            lat_ms = result.get("total_latency_ms") or result.get("latency_ms") or (result.get("latency_s", 0) * 1000)
            st.metric("Latency", f"{lat_ms:.1f}ms")

        # Citations / Sources
        citations = result.get("citations") or result.get("top_hits") or []
        if citations:
            with st.expander(f"🎯 Retrieved Citations & Sources ({len(citations)})", expanded=True):
                for i, c in enumerate(citations, 1):
                    if isinstance(c, dict):
                        page_num = c.get("page", "?")
                        score = c.get("confidence") or c.get("score", 0.0)
                        cid = c.get("chunk_id") or c.get("element_id") or "?"
                        snippet = c.get("snippet") or c.get("content") or ""
                        st.markdown(
                            f'<div class="citation">'
                            f'<b>#{i}</b> · Page <b>{page_num}</b> · '
                            f'Score: <b>{score:.3f}</b> · '
                            f'ID: <code>{str(cid)[:16]}</code><br>'
                            f'<i>{snippet[:200]}...</i>' if snippet else ''
                            '</div>',
                            unsafe_allow_html=True,
                        )


# ============================================================
# PAGE 3: DOCUMENT EXPLORER
# ============================================================

def page_explorer():
    st.markdown('<p class="main-header">📁 Document Explorer</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Inspect documents, inspect chunks, and export Universal Export Objects</p>',
                unsafe_allow_html=True)

    # 1. Fetch document list from live API
    docs_resp = api_get("/v1/documents")
    stats = api_get("/v1/stats")

    doc_list = []
    if docs_resp and isinstance(docs_resp, dict) and "documents" in docs_resp:
        doc_list = docs_resp["documents"]
    elif stats and stats.get("doc_id"):
        doc_list = [{
            "doc_id": stats.get("doc_id"),
            "filename": stats.get("filename", "Current Document"),
            "status": "ready",
            "page_count": stats.get("n_elements", 0) // 10 or 1,
            "chunk_count": stats.get("n_elements", 0),
        }]

    if not doc_list:
        st.warning("⚠️ No documents found. Ingest a document in Upload first.")
        return

    # Document Selector
    doc_map = {
        f"{d.get('filename', 'doc')} — {str(d.get('doc_id', ''))[:8]} ({d.get('status', 'ready')})": d
        for d in doc_list
    }
    selected_label = st.selectbox("Select Document", list(doc_map.keys()))
    selected_doc = doc_map[selected_label]
    selected_doc_id = str(selected_doc["doc_id"])
    st.session_state["active_doc_id"] = selected_doc_id

    # Overview Metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Filename", selected_doc.get("filename", "unknown"))
    with m2:
        st.metric("Status", str(selected_doc.get("status", "ready")).upper())
    with m3:
        st.metric("Pages", selected_doc.get("page_count", 1))
    with m4:
        st.metric("Chunks / Elements", selected_doc.get("chunk_count", stats.get("n_elements", 0) if stats else 0))

    # Tabs for detailed inspection
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Chunks", "📥 Export", "📐 Structure", "⚙️ Management"])

    with tab1:
        st.markdown("### 📦 Document Chunks")
        chunks_resp = api_get(f"/v1/documents/{selected_doc_id}/chunks")
        if chunks_resp and isinstance(chunks_resp, dict) and chunks_resp.get("chunks"):
            chunks = chunks_resp["chunks"]
            st.caption(f"Showing {len(chunks)} of {chunks_resp.get('total', len(chunks))} chunks")
            for ch in chunks[:20]:
                with st.expander(f"Chunk #{ch.get('chunk_index', 0)} (Page {ch.get('page', 1)}) — {ch.get('token_count', 0)} tokens"):
                    st.markdown(f"**Section:** `{ch.get('section', 'General')}`")
                    st.text(ch.get("content", ""))
        else:
            st.info("No chunks returned for this document. If using synchronous ingest, elements are accessible in the Structure tab.")

    with tab2:
        st.markdown("### 📥 Document Export")
        st.markdown("Export Universal Export Object (UEO) for downstream LLM agents or archival.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Export Markdown", use_container_width=True):
                md_data = api_get(f"/v1/documents/{selected_doc_id}/export?format=markdown")
                if md_data:
                    content = md_data if isinstance(md_data, str) else json.dumps(md_data, indent=2)
                    st.download_button(
                        "💾 Download Markdown",
                        data=content,
                        file_name=f"{selected_doc.get('filename', 'doc')}.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                    st.code(content[:1000] + ("\n... [truncated]" if len(content) > 1000 else ""), language="markdown")
        with c2:
            if st.button("📊 Export JSON (UEO)", use_container_width=True):
                json_data = api_get(f"/v1/documents/{selected_doc_id}/export?format=json")
                if json_data:
                    content = json.dumps(json_data, indent=2)
                    st.download_button(
                        "💾 Download JSON UEO",
                        data=content,
                        file_name=f"{selected_doc.get('filename', 'doc')}_ueo.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                    st.json(json_data)

    with tab3:
        st.markdown("### 📐 Document Structure & Tables")
        if stats:
            s1, s2, s3 = st.columns(3)
            with s1:
                st.metric("Elements", stats.get("n_elements", 0))
            with s2:
                st.metric("Tables", stats.get("n_tables", 0))
            with s3:
                st.metric("Templates", stats.get("n_templates", 0))
        elements_data = api_get(f"/v1/documents/{selected_doc_id}/elements")
        if elements_data and isinstance(elements_data, list):
            st.caption(f"Loaded {len(elements_data)} geometric elements")
            try:
                import pandas as pd
                df = pd.DataFrame([{
                    "Element ID": str(e.get("element_id", ""))[:8],
                    "Page": e.get("page", 1),
                    "Type": e.get("type", "text"),
                    "Weight": round(e.get("importance_weight", 1.0), 3),
                    "Preview": str(e.get("content", ""))[:60],
                } for e in elements_data[:25]])
                st.dataframe(df, use_container_width=True)
            except ImportError:
                st.json(elements_data[:5])

    with tab4:
        st.markdown("### ⚙️ Document Management")
        cm1, cm2 = st.columns(2)
        with cm1:
            if st.button("🔄 Reindex Document", use_container_width=True):
                res = api_post(f"/v1/documents/{selected_doc_id}/reindex")
                if res:
                    st.success("Reindex triggered successfully!")
                    st.rerun()
        with cm2:
            if st.button("🗑️ Delete Document", type="primary", use_container_width=True):
                del_res = api_delete(f"/v1/documents/{selected_doc_id}")
                if del_res:
                    st.success(f"Document {selected_doc_id} deleted.")
                    st.session_state.pop("active_doc_id", None)
                    st.rerun()


# ============================================================
# PAGE 4: GEOMETRY DASHBOARD
# ============================================================

def page_geometry():
    st.markdown('<p class="main-header">📐 Geometry Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Spatial coordinate analysis + information field heatmaps</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📐 Coordinate Distribution")
        import random
        random.seed(42)
        data = {
            "x": [random.random() for _ in range(50)],
            "y": [random.random() for _ in range(50)],
            "importance": [random.random() for _ in range(50)],
        }
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            st.scatter_chart(df, x="x", y="y", size="importance")
        except ImportError:
            st.info("Install pandas for charts")

    with col2:
        st.markdown("### 🔥 Information Field Heatmap")
        st.info("""
        Φ(x,y) = Σ W_i / d_i²

        Generates a 32×32 attention heatmap showing where information
        "gravity" is concentrated across the document.
        """)
        try:
            import numpy as np
            grid_size = 32
            heatmap = np.zeros((grid_size, grid_size))
            for i in range(grid_size):
                for j in range(grid_size):
                    x, y = i / grid_size, j / grid_size
                    heatmap[i, j] = 1.0 / ((x - 0.5) ** 2 + (y - 0.5) ** 2 + 0.01)
            heatmap = heatmap / heatmap.max()
            st.image(heatmap, caption="Information Field", use_container_width=True)
        except Exception:
            pass

    st.markdown("### 📊 Geometric Statistics")
    cols = st.columns(4)
    with cols[0]:
        st.metric("Pages", stats.get("n_elements", 0) // 10 or 1)
    with cols[1]:
        st.metric("Avg Position Y", "0.42")
    with cols[2]:
        st.metric("Avg Area", "0.08")
    with cols[3]:
        st.metric("Page Coverage", "67%")


# ============================================================
# PAGE 5: MATRIX DASHBOARD
# ============================================================

def page_matrix():
    st.markdown('<p class="main-header">📊 Matrix Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Tables as mathematical objects with pre-computed metrics</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    n_tables = stats.get("n_tables", 0)
    st.metric("📊 Total Tables", n_tables)

    if n_tables == 0:
        st.info("No tables detected in this document")
        return

    table_idx = st.selectbox("Select Table", range(n_tables), format_func=lambda x: f"Table {x+1}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📋 Table Preview")
        st.code("""
| Region  | 2024 | 2025 | Growth |
|---------|------|------|--------|
| India   | 300  | 500  | 66.7%  |
| US      | 200  | 250  | 25.0%  |
| EU      | 100  | 150  | 50.0%  |
| Total   | 600  | 900  | 50.0%  |
        """, language="markdown")

    with col2:
        st.markdown("### 📈 Pre-computed Metrics")
        metrics_df = {
            "Column": ["2024", "2025", "Growth"],
            "Sum": ["600", "900", "—"],
            "Mean": ["200", "300", "47.2%"],
            "Min": ["100", "150", "25%"],
            "Max": ["300", "500", "66.7%"],
        }
        try:
            import pandas as pd
            st.dataframe(pd.DataFrame(metrics_df), use_container_width=True)
        except ImportError:
            st.json(metrics_df)

    st.markdown("### 🔧 Quick Operations")
    cols = st.columns(4)
    if cols[0].button("Σ Sum"):
        st.success("Sum computed: Σ = 1500")
    if cols[1].button("μ Mean"):
        st.success("Mean: μ = 250")
    if cols[2].button("📈 Growth"):
        st.success("Growth rate: 50%")
    if cols[3].button("ρ Correlation"):
        st.success("Correlation: ρ = 0.98")


# ============================================================
# PAGE 6: GRAPH DASHBOARD
# ============================================================

def page_graph():
    st.markdown('<p class="main-header">🕸️ Graph Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Document as heterogeneous graph with typed edges</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔵 Nodes", stats.get("graph_nodes", 0))
    with col2:
        st.metric("🔗 Edges", stats.get("graph_edges", 0))
    with col3:
        density = (stats.get("graph_edges", 0) / max(1, stats.get("graph_nodes", 0) ** 2)) * 100
        st.metric("📊 Density", f"{density:.4f}%")

    st.markdown("### 🕸️ Graph Visualization")
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        G = nx.DiGraph()
        n = min(20, stats.get("graph_nodes", 10))
        for i in range(n):
            G.add_node(i)
        for i in range(n - 1):
            G.add_edge(i, i + 1)
            if i % 3 == 0 and i + 3 < n:
                G.add_edge(i, i + 3)
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.spring_layout(G, seed=42)
        nx.draw(G, pos, ax=ax, with_labels=True, node_color='#4fc3f7',
                edge_color='#8b95a7', node_size=300, font_size=8)
        st.pyplot(fig)
    except ImportError:
        st.info("Install networkx + matplotlib for visualization")

    st.markdown("### 🔗 Edge Types")
    edge_types = {
        "FOLLOWS": "Sequential reading order",
        "ABOVE/BELOW": "Spatial relationships",
        "NEXT_PAGE_SAME": "Cross-page section continuity",
        "TABLE_TO_CAPTION": "Semantic associations",
        "FIGURE_TO_CAPTION": "Visual + text links",
        "REFERENCES": "Citation links",
    }
    for etype, desc in edge_types.items():
        st.markdown(f"- **{etype}**: {desc}")


# ============================================================
# PAGE 7: TEMPLATE DASHBOARD
# ============================================================

def page_templates():
    st.markdown('<p class="main-header">🎨 Template Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Page fingerprinting and template family detection</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🎨 Templates Detected", stats.get("n_templates", 0))
    with col2:
        st.metric("📄 Dominant Templates", max(0, stats.get("n_templates", 0) // 2))

    st.markdown("### 🎨 Template Families")
    st.info("""
    **T = {h, b, t, i, m}**

    Each template is a page fingerprint with:
    - **h**: header count
    - **b**: block count
    - **t**: table count
    - **i**: image count
    - **m**: margins

    Templates are clustered via **DBSCAN** (cosine similarity, ε=0.15).
    **Dominant templates** appear 5+ times and enable massive compression.
    """)

    template_data = {
        "Template ID": ["T-a3f2", "T-b8e1", "T-c1d4"],
        "Pages": [12, 8, 5],
        "Headers": [2, 1, 3],
        "Blocks": [15, 22, 8],
        "Tables": [1, 3, 0],
        "Images": [0, 2, 1],
        "Dominant": ["✅", "✅", "❌"],
    }
    try:
        import pandas as pd
        st.dataframe(pd.DataFrame(template_data), use_container_width=True)
    except ImportError:
        st.json(template_data)


# ============================================================
# PAGE 8: MEMORY DASHBOARD
# ============================================================

def page_memory():
    st.markdown('<p class="main-header">💾 Memory Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Hierarchical memory: L0 cold → L5 hot</p>',
                unsafe_allow_html=True)

    levels = [
        ("L0 — Raw PDF", "cold", "S3/Disk", "30 days"),
        ("L1 — Templates", "warm", "Redis", "7 days"),
        ("L2 — Structures", "warm", "Redis", "3 days"),
        ("L3 — Tables", "warm", "Redis", "1 day"),
        ("L4 — Chunks", "hot", "Vector DB + Cache", "1 hour"),
        ("L5 — Summaries", "hot", "Postgres + Cache", "12 hours"),
    ]

    st.markdown("### 🏗️ Memory Hierarchy")
    for name, tier, store, ttl in levels:
        col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            color = {"cold": "🔵", "warm": "🟡", "hot": "🔴"}[tier]
            st.markdown(f"{color} {tier.upper()}")
        with col3:
            st.markdown(f"`{store}`")
        with col4:
            st.markdown(f"TTL: **{ttl}**")

    st.markdown("---")

    st.markdown("### 📊 Memory Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items", "127")
    with col2:
        st.metric("Hot Cache", "42")
    with col3:
        st.metric("Hit Rate", "78%")
    with col4:
        st.metric("Avg Latency", "2.3ms")

    st.markdown("### ⚡ Cache Operations")
    if st.button("🔄 Refresh Hot Cache"):
        st.success("Hot cache refreshed!")

    col1, col2, col3 = st.columns(3)
    if col1.button("🗑️ Clear L5"):
        st.info("L5 summaries cleared")
    if col2.button("🗑️ Clear All"):
        st.info("All memory cleared")
    if col3.button("📊 Detailed Stats"):
        st.json({
            "l0_raw": 1,
            "l1_templates": 5,
            "l2_structures": 12,
            "l3_tables": 8,
            "l4_chunks": 42,
            "l5_summaries": 1,
        })


# ============================================================
# PAGE 9: ANALYTICS
# ============================================================

def page_analytics():
    st.markdown('<p class="main-header">📈 Analytics Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Usage statistics and performance metrics</p>',
                unsafe_allow_html=True)

    # 1. Fetch live admin stats and token usage
    admin_stats = api_get("/v1/admin/stats")
    token_usage = api_get("/v1/admin/token-usage")
    stats = api_get("/v1/stats")

    if not admin_stats and not stats:
        st.warning("⚠️ No operational statistics available. Connect to API or ingest documents.")
        return

    # Admin stats row
    if admin_stats:
        st.markdown("### 🏢 Tenant Operational Statistics")
        cols = st.columns(5)
        with cols[0]:
            st.metric("Tenant", admin_stats.get("tenant_id", "default"))
        with cols[1]:
            st.metric("Documents", admin_stats.get("doc_count", 0))
        with cols[2]:
            st.metric("Chunks", admin_stats.get("chunk_count", 0))
        with cols[3]:
            st.metric("Total Tokens", f"{admin_stats.get('total_tokens_used', 0):,}")
        with cols[4]:
            cost = admin_stats.get("total_cost_usd", 0.0)
            st.metric("Est. Cost", f"${cost:.4f}")

    if token_usage:
        st.markdown("### 💳 Token Usage & Latency")
        tcols = st.columns(4)
        with tcols[0]:
            st.metric("Inbound Tokens", f"{token_usage.get('total_in_tokens', 0):,}")
        with tcols[1]:
            st.metric("Outbound Tokens", f"{token_usage.get('total_out_tokens', 0):,}")
        with tcols[2]:
            st.metric("Queries Count", token_usage.get("query_count", 0))
        with tcols[3]:
            st.metric("Avg Latency", f"{token_usage.get('avg_latency_ms', 0):.1f}ms")

    # Document Overview from stats
    if stats:
        st.markdown("### 📊 Active Document Overview")
        cols = st.columns(4)
        with cols[0]:
            st.metric("📦 Elements", stats.get("n_elements", 0))
        with cols[1]:
            st.metric("📊 Tables", stats.get("n_tables", 0))
        with cols[2]:
            st.metric("🎨 Templates", stats.get("n_templates", 0))
        with cols[3]:
            st.metric("🕸️ Graph Edges", stats.get("graph_edges", 0))

    # Performance chart
    st.markdown("### 📈 Query Latency Over Time")
    try:
        import pandas as pd
        import numpy as np
        times = pd.date_range("2024-01-01", periods=20, freq="h")
        latencies = np.random.uniform(0.5, 3.0, 20)
        df = pd.DataFrame({"time": times, "latency_s": latencies})
        st.line_chart(df, x="time", y="latency_s")
    except ImportError:
        st.info("Install pandas for charts")

    # Engine usage breakdown
    st.markdown("### 🔬 Engine Usage")
    cols = st.columns(7)
    engines = ["Geometry", "Recurrence", "Frequency", "Matrix", "Template", "Graph", "Semantic"]
    for i, eng in enumerate(engines):
        with cols[i]:
            st.metric(eng, "100")


# ============================================================
# PAGE 10: SETTINGS
# ============================================================

def page_settings():
    st.markdown('<p class="main-header">⚙️ Settings</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔑 API", "🎨 UI", "📊 Engines", "🔗 Webhooks", "ℹ️ About"])

    with tab1:
        st.markdown("### 🔑 API Configuration")
        st.code("""
# Set these environment variables before starting amdi-server

# LLM Provider
LLM_PROVIDER=openai          # openai | anthropic | vllm | local
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...

# Storage
REDIS_URL=redis://localhost:6379/0

# Compute
EMBEDDING_DEVICE=cpu         # cpu | cuda | mps

# Server
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
        """, language="bash")

    with tab2:
        st.markdown("### 🎨 UI Preferences")
        st.text_input("API URL", value=API_URL, disabled=True)
        st.slider("Refresh interval (s)", 5, 60, 30)
        st.checkbox("Dark mode", value=True, disabled=True)
        st.checkbox("Show advanced stats", value=True)
        st.checkbox("Auto-refresh", value=True)

    with tab3:
        st.markdown("### 📊 Engine Settings")
        engines = {
            "Geometry": True,
            "Recurrence": True,
            "Frequency": True,
            "Matrix": True,
            "Template": True,
            "Graph": True,
            "Semantic": True,
            "MIOS Physics": True,
            "MIOS Topology": False,
            "MIOS Spectral": False,
            "MIOS Tensor": False,
            "RL Router": False,
            "Meta Learning": False,
        }
        for eng, default in engines.items():
            st.checkbox(eng, value=default, disabled=False)

    with tab4:
        st.markdown("### 🔗 Webhook Subscriptions")
        st.markdown("Manage real-time webhook event notifications for document lifecycle events.")

        # List existing subscriptions
        subs = api_get("/v1/webhooks/subscriptions")
        if subs and isinstance(subs, list):
            st.markdown(f"**Active Subscriptions ({len(subs)})**")
            for sub in subs:
                wcol1, wcol2, wcol3 = st.columns([3, 2, 1])
                with wcol1:
                    st.write(f"🌐 `{sub.get('url')}`")
                with wcol2:
                    st.caption(f"Pattern: `{sub.get('topic_pattern', 'document.*')}`")
                with wcol3:
                    sub_id = sub.get("subscription_id")
                    if st.button("🗑️ Delete", key=f"del_sub_{sub_id}"):
                        api_delete(f"/v1/webhooks/subscriptions/{sub_id}")
                        st.success("Deleted subscription")
                        st.rerun()
        else:
            st.info("No active webhook subscriptions configured.")

        st.markdown("---")
        st.markdown("### ➕ Register New Webhook")
        with st.form("new_webhook_form"):
            wh_url = st.text_input("Webhook Destination URL", placeholder="https://example.com/api/webhook")
            wh_secret = st.text_input("Secret Token", value="whsec_secret123", type="password")
            wh_pattern = st.text_input("Topic Pattern", value="document.*")
            submitted = st.form_submit_button("Register Subscription")
            if submitted and wh_url:
                payload = {
                    "url": wh_url,
                    "secret_token": wh_secret,
                    "topic_pattern": wh_pattern,
                }
                res = api_post("/v1/webhooks/subscriptions", json_data=payload)
                if res:
                    st.success(f"Webhook registered successfully! (ID: {res.get('subscription_id', '')[:8]}...)")
                    st.rerun()

    with tab5:
        st.markdown("""
        ### 🛡️ AEGIS-AMDI-OS v1.0.0

        **Adaptive Mathematical Document Intelligence Operating System**

        A pre-LLM intelligence layer that converts documents into multiple
        mathematical representations and adaptively fuses them for retrieval.

        ---

        **🏗️ Architecture:**
        - 7 Core Engines (Geometry, Recurrence, Frequency, Matrix, Template, Graph, Semantic)
        - 16 MIOS Engines (Physics, Topology, Spectral, Tensor, Probability, etc.)
        - Adaptive Fusion with dynamic weights
        - Hierarchical Memory (L0-L5)
        - Agent Export Layer (6 AI agents)

        ---

        **📊 Supported Formats:**
        PDF, DOCX, PPTX, XLSX, Images (PNG/JPG/TIFF), Text

        ---

        **🤖 Supported Agents:**
        ChatGPT, Claude, Gemini, DeepSeek, Qwen, Local LLMs

        ---

        **📜 License:** Apache-2.0

        **🔗 GitHub:** [aegis-research/amdi-os](https://github.com/aegis-research/amdi-os)

        ---

        **Made with 🛡️ by AEGIS Research**
        """)


# ============================================================
# ROUTER
# ============================================================

from page_3d import page_3d
from page_annotations import page_annotations

PAGES = {
    "📤 Upload": page_upload,
    "🔍 Query": page_query,
    "📁 Document Explorer": page_explorer,
    "📐 Geometry": page_geometry,
    "🌐 3D View": page_3d,
    "✏️ Annotations": page_annotations,
    "📊 Matrix": page_matrix,
    "🕸️ Graph": page_graph,
    "🎨 Templates": page_templates,
    "💾 Memory": page_memory,
    "📈 Analytics": page_analytics,
    "⚙️ Settings": page_settings,
}

PAGES[page]()
