"""
AEGIS-AMDI-OS — 3D Document Geometry Page
=========================================
Dashboard page for interactive 3D document geometry, coordinate mapping,
bounding volumes, connections graph, stacked page planes, and information field heatmaps.
"""
from __future__ import annotations

import streamlit as st
import numpy as np
import requests

from src.engines.geometry.element import GeometricElement, BoundingBox, ElementType
from src.engines.geometry_3d import Geometry3DEngine
from src.visualization.visualization_3d import Visualization3D


def page_3d():
    st.markdown('<p class="main-header">🌐 3D Document Visualization</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Interactive 3D geometry engine, stacked page planes, and information fields</p>',
                unsafe_allow_html=True)

    # 1. Fetch document stats to check if active doc exists
    from app import api_get
    stats = api_get("/v1/stats")
    if not stats:
        st.warning("⚠️ No document ingested. Go to Upload first.")
        return

    doc_id = stats.get("doc_id")
    filename = stats.get("filename", "document")
    st.success(f"📄 Active Document: **{filename}** (ID: `{doc_id[:8]}...`)")

    # 2. Fetch all elements for this document from the API
    elements_json = api_get(f"/v1/documents/{doc_id}/elements")
    if not elements_json:
        st.error("Failed to load document elements.")
        return

    # 3. Reconstruct GeometricElement objects
    elements = []
    for el_dict in elements_json:
        bbox = None
        if el_dict.get("bbox"):
            x0, y0, x1, y1 = el_dict["bbox"]
            bbox = BoundingBox(x0=x0, y0=y0, x1=x1, y1=y1)
        
        el = GeometricElement(
            element_id=el_dict["element_id"],
            doc_id=el_dict["doc_id"],
            page=el_dict["page"],
            type=ElementType(el_dict["type"]),
            content=el_dict["content"],
            bbox=bbox,
            importance_weight=el_dict.get("importance_weight", 1.0)
        )
        if el_dict.get("section"):
            el.section = el_dict["section"]
        elements.append(el)

    total_pages = max([e.page for e in elements]) if elements else 1

    # 4. Lift elements to 3D representation
    geo_engine = Geometry3DEngine()
    elements_3d = geo_engine.lift_to_3d(elements, total_pages)

    if not elements_3d:
        st.info("No elements with bounding boxes available for 3D visualization.")
        return

    # 5. UI Controls Sidebar/Columns
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("### ⚙️ View Controls")
        
        view_mode = st.selectbox(
            "Visualization Mode",
            [
                "3D Scatter Points",
                "3D Bounding Volumes",
                "3D Relationships Graph",
                "Stacked Page Planes",
                "Information Field Slice",
            ]
        )

        color_by = st.selectbox(
            "Color Nodes By",
            ["type", "page", "importance"],
            disabled=(view_mode in ["3D Bounding Volumes", "Information Field Slice"])
        )

        size_by = st.selectbox(
            "Size Nodes By",
            ["importance", "uniform"],
            disabled=(view_mode in ["3D Bounding Volumes", "Information Field Slice"])
        )

        st.markdown("---")

        if view_mode == "Information Field Slice":
            st.markdown("#### Heatmap Slice Configuration")
            plane = st.selectbox("Contour Plane", ["xy", "xz", "yz"])
            
            page_filter = None
            if plane == "xy":
                use_page_filter = st.checkbox("Restrict to specific page", value=False)
                if use_page_filter:
                    page_filter = st.number_input("Page Number", 1, total_pages, 1)
            
            resolution = st.slider("Heatmap Resolution", 16, 64, 32, step=8)
            z_slice = st.slider("Z-axis Coordinate (Slice plane)", 0.0, 1.0, 0.5)

        st.markdown("### 📊 3D Engine Statistics")
        stats_3d = geo_engine.statistics(elements_3d)
        st.markdown(f"**Total 3D Nodes**: `{stats_3d.get('n_elements', 0)}`")
        st.markdown(f"**Pages Stacked**: `{stats_3d.get('n_pages', 0)}`")
        st.markdown(f"**Avg. Importance**: `{stats_3d.get('mean_importance', 0.0):.3f}`")

    # 6. Render 3D Figure
    viz_engine = Visualization3D()
    fig = None

    with col2:
        with st.spinner("Generating 3D interactive model..."):
            if view_mode == "3D Scatter Points":
                fig = viz_engine.scatter_3d(
                    elements_3d,
                    color_by=color_by,
                    size_by=size_by,
                    title=f"3D Document Geometry Scatter — {filename}"
                )
            elif view_mode == "3D Bounding Volumes":
                fig = viz_engine.boxes_3d(
                    elements_3d,
                    title=f"3D Bounding Volumes — {filename}"
                )
            elif view_mode == "3D Relationships Graph":
                connections = geo_engine.build_connections(elements_3d, same_page=True)
                fig = viz_engine.graph_3d(
                    elements_3d,
                    connections,
                    title=f"3D Spatial Proximity Graph — {filename}"
                )
            elif view_mode == "Stacked Page Planes":
                fig = viz_engine.stacked_pages_3d(
                    elements_3d,
                    title=f"Stacked 3D Page Planes — {filename}"
                )
            elif view_mode == "Information Field Slice":
                grid_x, grid_y, heatmap = geo_engine.field_heatmap_3d(
                    elements_3d,
                    plane=plane,
                    page=page_filter,
                    resolution=resolution
                )
                fig = viz_engine.heatmap_slice_3d(
                    grid_x,
                    grid_y,
                    heatmap,
                    plane=plane,
                    z_val=z_slice,
                    title=f"3D Field Slice ({plane.upper()}-plane at {'Z='+str(z_slice) if plane=='xy' else 'center'})"
                )

        if fig:
            st.plotly_chart(fig, use_container_width=True, theme=None)
        else:
            st.error("Visualization engine failed to construct the Plotly figure.")
