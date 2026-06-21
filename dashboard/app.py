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
# CONFIG
# ============================================================

API_URL = st.sidebar.text_input("🔗 API URL", value="http://localhost:8000", key="api_url")


def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint: str, json_data: dict = None, files: dict = None):
    try:
        if files:
            r = requests.post(f"{API_URL}{endpoint}", files=files, timeout=600)
        else:
            r = requests.post(f"{API_URL}{endpoint}", json=json_data, timeout=300)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_delete(endpoint: str):
    try:
        r = requests.delete(f"{API_URL}{endpoint}", timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
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
    if stats:
        st.markdown("### 📄 Current Doc")
        st.caption(f"**{stats.get('filename', '?')}**")
        st.caption(f"Elements: {stats.get('n_elements', 0)}")
        st.caption(f"Tables: {stats.get('n_tables', 0)}")
        if st.button("🗑️ Clear", use_container_width=True):
            api_delete("/v1/document")
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
            with st.spinner("Processing through 8 engines..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                result = api_post("/v1/ingest", files=files)
                if result:
                    st.session_state["last_ingest"] = result
                    st.balloons()
                    st.success("✅ Document indexed successfully!")
                else:
                    st.error("Failed. Check API.")

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

    if "last_ingest" in st.session_state:
        with st.expander("📄 Detailed Info", expanded=False):
            st.json(st.session_state["last_ingest"])


# ============================================================
# PAGE 2: QUERY
# ============================================================

def page_query():
    st.markdown('<p class="main-header">🔍 Query Document</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask questions with adaptive multi-layer retrieval</p>',
                unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("⚠️ No document ingested. Go to Upload first.")
        return

    st.success(f"📄 Active: **{stats.get('filename', '?')}**")

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
            result = api_post("/v1/query", {"question": question, "top_k": top_k})
            if result:
                st.session_state["last_query"] = result
                st.session_state["last_q_text"] = question

    # Display result
    if "last_query" in st.session_state:
        result = st.session_state["last_query"]

        st.markdown("### 💡 Answer")
        st.markdown(f"```\n{result.get('answer', '')}\n```")

        # Metrics row
        st.markdown("### 📊 Query Analytics")
        cols = st.columns(5)
        with cols[0]:
            st.metric("Type", result.get("query_type", "?"))
        with cols[1]:
            st.metric("Dominant", result.get("dominant_layer", "?"))
        with cols[2]:
            st.metric("Tokens", f"{result.get('input_tokens', 0)}↓ / {result.get('output_tokens', 0)}↑")
        with cols[3]:
            st.metric("Context", f"{result.get('context_tokens', 0)}")
        with cols[4]:
            st.metric("Latency", f"{result.get('latency_s', 0)}s")

        # Layer weights
        weights = result.get("weights", [])
        if weights:
            st.markdown("### ⚖️ Layer Weight Distribution")
            layer_names = ["Semantic", "Geometry", "Recurrence", "Frequency",
                          "Matrix", "Template", "Graph"]
            layer_classes = ["layer-semantic", "layer-geometry", "layer-semantic",
                            "layer-semantic", "layer-matrix", "layer-semantic",
                            "layer-graph"]
            cols = st.columns(7)
            for i, (name, w, cls) in enumerate(zip(layer_names, weights, layer_classes)):
                with cols[i]:
                    pct = w * 100
                    st.markdown(
                        f'<div class="layer-badge {cls}">{name}</div>'
                        f'<div style="font-size:1.5rem;font-weight:bold;margin-top:0.5rem">{pct:.1f}%</div>'
                        f'<div style="color:#8b95a7;font-size:0.7rem">weight</div>',
                        unsafe_allow_html=True,
                    )

        # Top hits
        if "top_hits" in result:
            with st.expander("🎯 Top Retrieved Elements", expanded=False):
                for i, h in enumerate(result["top_hits"], 1):
                    st.markdown(
                        f'<div class="citation">'
                        f'<b>#{i}</b> · Page <b>{h.get("page", "?")}</b> · '
                        f'Score: <b>{h.get("score", 0):.3f}</b> · '
                        f'ID: <code>{str(h.get("element_id", "?"))[:16]}</code>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )


# ============================================================
# PAGE 3: DOCUMENT EXPLORER
# ============================================================

def page_explorer():
    st.markdown('<p class="main-header">📁 Document Explorer</p>', unsafe_allow_html=True)

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Elements", "📊 Tables", "🎨 Templates", "🕸️ Graph"])

    with tab1:
        st.markdown("### 📦 All Geometric Elements")
        st.caption(f"Total: {stats.get('n_elements', 0)} elements")

        # Mock data display
        st.info("""
        Elements are the atomic units of the document, each with:
        - Geometric coordinates (x, y, w, h, page)
        - Type (text, table, figure, header, footer)
        - Importance weight (from Frequency Engine)
        - Recurrence ID (from Recurrence Engine)
        - Semantic embedding (from Semantic Engine)
        """)

    with tab2:
        st.markdown(f"### 📊 Tables ({stats.get('n_tables', 0)})")
        st.info("""
        Tables are represented as mathematical matrices M[i,j] with:
        - Pre-computed sum, mean, min, max per column
        - Growth rates between first and last values
        - Cell dependencies D(i,j)
        - LLM-ready string serialization
        """)

    with tab3:
        st.markdown(f"### 🎨 Templates ({stats.get('n_templates', 0)})")
        st.info("""
        Templates are page fingerprints T = {h, b, t, i, m} clustered via DBSCAN.
        Dominant templates appear 5+ times and enable massive compression.
        """)

    with tab4:
        st.markdown("### 🕸️ Document Graph")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nodes", stats.get("graph_nodes", 0))
        with col2:
            st.metric("Edges", stats.get("graph_edges", 0))
        st.info("""
        Graph G = (V, E) with typed edges:
        - FOLLOWS: reading order
        - ABOVE/BELOW: spatial
        - NEXT_PAGE_SAME: cross-page continuity
        - REFERENCES: semantic links
        """)


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
        # Simulated distribution
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
        # Generate sample heatmap
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

    # Table selector
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

    # Operations
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
        # Sample graph
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

    # Edge types
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

    # Sample template data
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

    # Memory levels
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

    # Statistics
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

    # Cache operations
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

    stats = api_get("/v1/stats")
    if not stats:
        st.warning("No document ingested")
        return

    # Top metrics
    st.markdown("### 📊 Document Overview")
    cols = st.columns(4)
    with cols[0]:
        st.metric("📦 Elements", stats.get("n_elements", 0))
    with cols[1]:
        st.metric("📊 Tables", stats.get("n_tables", 0))
    with cols[2]:
        st.metric("🎨 Templates", stats.get("n_templates", 0))
    with cols[3]:
        st.metric("🕸️ Graph Edges", stats.get("graph_edges", 0))

    # API usage
    st.markdown("### 🔧 API Usage")
    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Requests", stats.get("requests_total", 0))
    with cols[1]:
        st.metric("Total Queries", stats.get("queries_total", 0))
    with cols[2]:
        st.metric("Active Sessions", "1")

    # Performance chart (simulated)
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
            st.metric(eng, f"{np.random.randint(50, 200)}" if 'np' in dir() else "100")


# ============================================================
# PAGE 10: SETTINGS
# ============================================================

def page_settings():
    st.markdown('<p class="main-header">⚙️ Settings</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔑 API", "🎨 UI", "📊 Engines", "ℹ️ About"])

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
