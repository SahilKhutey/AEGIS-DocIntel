"""
AEGIS-AMDI-OS — 3D Visualization Engine
==========================================
Plotly-based renderers for 3D document representations.

Visualizations:
- 3D scatter of elements
- 3D boxes (line segments) for bounding volumes
- 3D connection graph (lines)
- Field heatmaps on 3D slices
- Multi-page stacks
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None

logger = logging.getLogger(__name__)


class Visualization3D:
    """
    3D visualization builder using Plotly.
    """

    def __init__(self):
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not installed. 3D visualizations unavailable.")

    # ============================================================
    # SCATTER: 3D points
    # ============================================================

    def scatter_3d(
        self,
        elements: list,
        color_by: str = "type",
        size_by: str = "importance",
        title: str = "3D Document Geometry",
    ) -> Any:
        """
        Render 3D scatter of document elements.
        """
        if not PLOTLY_AVAILABLE:
            return None

        if not elements:
            return go.Figure().update_layout(title="No elements")

        # Extract coordinates
        xs = [e.x for e in elements]
        ys = [e.y for e in elements]
        zs = [e.z for e in elements]
        pages = [e.page for e in elements]
        texts = [e.text for e in elements]
        types = [e.element_type.value for e in elements]

        hover_texts = []
        for e in elements:
            snippet = e.text[:60] + "..." if len(e.text) > 60 else e.text
            hover_texts.append(
                f"Page: {e.page}<br>"
                f"Type: {e.element_type.value}<br>"
                f"Section: {e.section or 'None'}<br>"
                f"Weight: {e.importance:.2f}<br>"
                f"Content: {snippet}"
            )

        # Color mapping
        if color_by == "type":
            unique_types = sorted(set(types))
            color_map = {
                t: f"hsl({i * 360 / max(len(unique_types), 1)}, 70%, 60%)"
                for i, t in enumerate(unique_types)
            }
            colors = [color_map[t] for t in types]
        elif color_by == "page":
            max_p = max(pages) if pages else 1
            colors = [f"hsl({(p - 1) * 360 / max_p}, 70%, 60%)" for p in pages]
        elif color_by == "importance":
            colors = [e.importance for e in elements]
        else:
            colors = ["#4fc3f7"] * len(elements)

        # Size mapping
        if size_by == "importance":
            sizes = [max(5, min(25, e.importance * 20)) for e in elements]
        else:
            sizes = [10] * len(elements)

        fig = go.Figure()
        
        scatter_trace = go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='Viridis' if color_by == "importance" else None,
                opacity=0.8,
                line=dict(width=1, color='rgba(255, 255, 255, 0.5)')
            ),
            text=hover_texts,
            hoverinfo='text',
            name='Elements'
        )
        
        fig.add_trace(scatter_trace)

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(title='X (width)', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                yaxis=dict(title='Y (height)', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                zaxis=dict(title='Z (page)', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                aspectratio=dict(x=1, y=1.2, z=1.5),
            ),
            margin=dict(r=0, l=0, b=0, t=40),
            paper_bgcolor='#0a0e1a',
            font_color='#f8fafc'
        )

        return fig

    # ============================================================
    # BOXES: 3D bounding boxes
    # ============================================================

    def boxes_3d(
        self,
        elements: list,
        title: str = "3D Bounding Volumes",
    ) -> Any:
        """
        Draw 3D bounding boxes for document elements.
        Grouped by type to support correct coloring.
        """
        if not PLOTLY_AVAILABLE:
            return None

        fig = go.Figure()

        if not elements:
            return fig.update_layout(title="No elements")

        # Group elements by type
        by_type = {}
        for e in elements:
            by_type.setdefault(e.element_type, []).append(e)

        for el_type, type_elems in by_type.items():
            bx, by, bz = [], [], []
            hover_texts = []
            
            for e in type_elems:
                c = e.to_corners()
                # Trace sequence: bottom loop -> top loop -> pillars
                # 0->1->2->3->0 -> 4->5->6->7->4
                x_coords = [c[0][0], c[1][0], c[2][0], c[3][0], c[0][0], c[4][0], c[5][0], c[6][0], c[7][0], c[4][0], None, c[1][0], c[5][0], None, c[2][0], c[6][0], None, c[3][0], c[7][0], None]
                y_coords = [c[0][1], c[1][1], c[2][1], c[3][1], c[0][1], c[4][1], c[5][1], c[6][1], c[7][1], c[4][1], None, c[1][1], c[5][1], None, c[2][1], c[6][1], None, c[3][1], c[7][1], None]
                z_coords = [c[0][2], c[1][2], c[2][2], c[3][2], c[0][2], c[4][2], c[5][2], c[6][2], c[7][2], c[4][2], None, c[1][2], c[5][2], None, c[2][2], c[6][2], None, c[3][2], c[7][2], None]
                
                bx.extend(x_coords)
                by.extend(y_coords)
                bz.extend(z_coords)

            # Draw trace for this type
            color = type_elems[0].color
            fig.add_trace(go.Scatter3d(
                x=bx, y=by, z=bz,
                mode='lines',
                line=dict(color=color, width=2),
                name=el_type.value,
                hoverinfo='none'
            ))

        # Add centers as scatter points for hover text
        xs = [e.x for e in elements]
        ys = [e.y for e in elements]
        zs = [e.z for e in elements]
        colors = [e.color for e in elements]
        
        hover_texts = []
        for e in elements:
            snippet = e.text[:60] + "..." if len(e.text) > 60 else e.text
            hover_texts.append(
                f"Page: {e.page}<br>"
                f"Type: {e.element_type.value}<br>"
                f"Section: {e.section or 'None'}<br>"
                f"Content: {snippet}"
            )

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(size=4, color=colors, opacity=0.8),
            text=hover_texts,
            hoverinfo='text',
            showlegend=False
        ))

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(title='X', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                yaxis=dict(title='Y', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                zaxis=dict(title='Z', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                aspectratio=dict(x=1, y=1.2, z=1.5),
            ),
            margin=dict(r=0, l=0, b=0, t=40),
            paper_bgcolor='#0a0e1a',
            font_color='#f8fafc'
        )

        return fig

    # ============================================================
    # GRAPH: 3D Network
    # ============================================================

    def graph_3d(
        self,
        elements: list,
        connections: list,
        title: str = "3D Document Network",
    ) -> Any:
        """
        Render 3D document graph with elements as nodes and connections as edges.
        """
        if not PLOTLY_AVAILABLE:
            return None

        fig = go.Figure()

        if not elements:
            return fig.update_layout(title="No elements")

        # 1. Draw connections (grouped by type)
        edges_by_type = {}
        for conn in connections:
            edges_by_type.setdefault(conn.edge_type, []).append(conn)

        colors_by_type = {
            "spatial_proximity": "#60a5fa",  # blue
            "next_page": "#fbbf24",          # amber
            "follows": "#10b981",            # emerald
            "references": "#ec4899",         # pink
        }

        for etype, conns in edges_by_type.items():
            ex, ey, ez = [], [], []
            for conn in conns:
                ex.extend([conn.src_pos[0], conn.dst_pos[0], None])
                ey.extend([conn.src_pos[1], conn.dst_pos[1], None])
                ez.extend([conn.src_pos[2], conn.dst_pos[2], None])
                
            color = colors_by_type.get(etype, "#a78bfa")
            fig.add_trace(go.Scatter3d(
                x=ex, y=ey, z=ez,
                mode='lines',
                line=dict(color=color, width=1.5),
                name=etype,
                hoverinfo='none'
            ))

        # 2. Draw nodes
        xs = [e.x for e in elements]
        ys = [e.y for e in elements]
        zs = [e.z for e in elements]
        colors = [e.color for e in elements]
        
        hover_texts = []
        for e in elements:
            snippet = e.text[:60] + "..." if len(e.text) > 60 else e.text
            hover_texts.append(
                f"Page: {e.page}<br>"
                f"Type: {e.element_type.value}<br>"
                f"Content: {snippet}"
            )

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(
                size=8,
                color=colors,
                opacity=0.9,
                line=dict(width=1, color='rgba(255, 255, 255, 0.4)')
            ),
            text=hover_texts,
            hoverinfo='text',
            name='Nodes'
        ))

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(title='X', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                yaxis=dict(title='Y', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                zaxis=dict(title='Z', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                aspectratio=dict(x=1, y=1.2, z=1.5),
            ),
            margin=dict(r=0, l=0, b=0, t=40),
            paper_bgcolor='#0a0e1a',
            font_color='#f8fafc'
        )

        return fig

    # ============================================================
    # STACKED PAGES: planes stack
    # ============================================================

    def stacked_pages_3d(
        self,
        elements: list,
        title: str = "Stacked 3D Page Planes",
    ) -> Any:
        """
        Visualize document as horizontal page planes in 3D.
        """
        if not PLOTLY_AVAILABLE:
            return None

        fig = go.Figure()

        if not elements:
            return fig.update_layout(title="No elements")

        # Get unique pages
        unique_pages = sorted(list(set(e.page for e in elements)))
        max_pages = max(unique_pages) if unique_pages else 1

        # Draw a plane for each page
        for p in unique_pages:
            z_val = (p - 1) / max_pages
            # 3D surface representing a flat plane [0, 1] x [0, 1]
            px = [0, 1, 1, 0]
            py = [0, 0, 1, 1]
            pz = [z_val, z_val, z_val, z_val]
            
            fig.add_trace(go.Mesh3d(
                x=px, y=py, z=pz,
                color='rgba(148, 163, 184, 0.1)',
                opacity=0.3,
                name=f"Page {p}",
                showlegend=True
            ))

        # Draw elements as points on the planes
        xs = [e.x for e in elements]
        ys = [e.y for e in elements]
        zs = [e.z for e in elements]
        colors = [e.color for e in elements]

        hover_texts = []
        for e in elements:
            snippet = e.text[:60] + "..." if len(e.text) > 60 else e.text
            hover_texts.append(
                f"Page: {e.page}<br>"
                f"Type: {e.element_type.value}<br>"
                f"Content: {snippet}"
            )

        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='markers',
            marker=dict(
                size=6,
                color=colors,
                opacity=0.9
            ),
            text=hover_texts,
            hoverinfo='text',
            name='Elements'
        ))

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(title='X', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                yaxis=dict(title='Y', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                zaxis=dict(title='Z (Pages)', range=[-0.1, 1.1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                aspectratio=dict(x=1, y=1.2, z=1.5),
            ),
            margin=dict(r=0, l=0, b=0, t=40),
            paper_bgcolor='#0a0e1a',
            font_color='#f8fafc'
        )

        return fig

    # ============================================================
    # FIELD HEATMAP: 3D Surface
    # ============================================================

    def heatmap_slice_3d(
        self,
        grid_x: np.ndarray,
        grid_y: np.ndarray,
        heatmap: np.ndarray,
        plane: str = "xy",
        z_val: float = 0.5,
        title: str = "3D Information Field Slice",
    ) -> Any:
        """
        Draw a surface heatmap in 3D representing a slice.
        """
        if not PLOTLY_AVAILABLE:
            return None

        # Normalize heatmap for display
        hm_max = heatmap.max()
        if hm_max > 0:
            heatmap = heatmap / hm_max

        fig = go.Figure()

        if plane == "xy":
            # Surface lies horizontally at z = z_val
            # Plotly Surface requires 2D arrays for x, y, and z.
            # To draw a flat surface with colored values:
            # We set z to a constant 2D matrix of value z_val, and color it using surfacecolor=heatmap
            z_matrix = np.full_like(grid_x, z_val)
            fig.add_trace(go.Surface(
                x=grid_x,
                y=grid_y,
                z=z_matrix,
                surfacecolor=heatmap,
                colorscale='Hot',
                opacity=0.8,
                colorbar=dict(title="Intensity", len=0.6)
            ))
        elif plane == "xz":
            # Surface lies vertically at y = 0.5
            y_matrix = np.full_like(grid_x, 0.5)
            fig.add_trace(go.Surface(
                x=grid_x,
                y=y_matrix,
                z=grid_y,  # grid_y here represents z coordinates
                surfacecolor=heatmap,
                colorscale='Hot',
                opacity=0.8,
                colorbar=dict(title="Intensity", len=0.6)
            ))
        else: # yz
            # Surface lies vertically at x = 0.5
            x_matrix = np.full_like(grid_x, 0.5)
            fig.add_trace(go.Surface(
                x=x_matrix,
                y=grid_x,
                z=grid_y,
                surfacecolor=heatmap,
                colorscale='Hot',
                opacity=0.8,
                colorbar=dict(title="Intensity", len=0.6)
            ))

        fig.update_layout(
            title=title,
            scene=dict(
                xaxis=dict(title='X', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                yaxis=dict(title='Y', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                zaxis=dict(title='Z', range=[0, 1], gridcolor='#334155', backgroundcolor='#0a0e1a'),
                aspectratio=dict(x=1, y=1.2, z=1.5),
            ),
            margin=dict(r=0, l=0, b=0, t=40),
            paper_bgcolor='#0a0e1a',
            font_color='#f8fafc'
        )

        return fig
