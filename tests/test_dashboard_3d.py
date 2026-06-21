"""Tests for 3D Geometry and 3D Visualization engines."""
import sys
from pathlib import Path
import pytest
import numpy as np

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.engines.geometry.element import GeometricElement, BoundingBox, ElementType
from src.engines.geometry_3d import Geometry3DEngine, Element3D, Point3D, Connection3D
from src.visualization.visualization_3d import Visualization3D


def test_data_classes_3d():
    """Test 3D engine dataclasses initialization and methods."""
    pt = Point3D(x=0.1, y=0.2, z=0.3, label="test")
    assert pt.x == 0.1
    assert pt.y == 0.2
    assert pt.z == 0.3
    assert pt.label == "test"

    el = Element3D(
        element_id="el1",
        element_type=ElementType.TEXT,
        x=0.5, y=0.5, z=0.2,
        width=0.2, height=0.1, depth=0.1
    )
    corners = el.to_corners()
    assert corners.shape == (8, 3)
    # verify corner coordinate logic
    assert np.allclose(corners[0], [0.4, 0.45, 0.15])  # x - hw, y - hh, z - hd

    conn = Connection3D(
        src_id="el1", dst_id="el2",
        src_pos=(0.5, 0.5, 0.2), dst_pos=(0.6, 0.6, 0.2),
        edge_type="spatial_proximity"
    )
    assert conn.src_id == "el1"
    assert conn.dst_pos == (0.6, 0.6, 0.2)


def test_geometry_3d_engine_lifting():
    """Test lifting 2D elements to 3D space."""
    elements = [
        GeometricElement(
            element_id="e1",
            page=1,
            type=ElementType.TEXT,
            content="Hello world",
            bbox=BoundingBox(x0=0.1, y0=0.1, x1=0.3, y1=0.2),
            importance_weight=0.8
        ),
        GeometricElement(
            element_id="e2",
            page=2,
            type=ElementType.TABLE,
            content="Table content",
            bbox=BoundingBox(x0=0.4, y0=0.3, x1=0.7, y1=0.6),
            importance_weight=1.0
        )
    ]
    
    engine = Geometry3DEngine()
    elements_3d = engine.lift_to_3d(elements, total_pages=2)
    
    assert len(elements_3d) == 2
    assert elements_3d[0].element_id == "e1"
    assert elements_3d[0].element_type == ElementType.TEXT
    assert elements_3d[0].page == 1
    assert elements_3d[0].z == 0.0  # (page - 1) / total_pages = 0 / 2 = 0
    assert elements_3d[1].z == 0.5  # (page - 1) / total_pages = 1 / 2 = 0.5


def test_geometry_3d_engine_computations():
    """Test 3D distance, neighbor queries, and connection graph."""
    engine = Geometry3DEngine()
    elements_3d = [
        Element3D("e1", ElementType.TEXT, 0.2, 0.2, 0.0, 0.1, 0.1, 0.1, page=1),
        Element3D("e2", ElementType.TEXT, 0.3, 0.2, 0.0, 0.1, 0.1, 0.1, page=1),
        Element3D("e3", ElementType.TEXT, 0.2, 0.3, 0.5, 0.1, 0.1, 0.1, page=2),
    ]

    # distances
    dist_matrix = engine.compute_distances_3d(elements_3d)
    assert dist_matrix.shape == (3, 3)
    assert np.isclose(dist_matrix[0, 1], 0.1)

    # neighbors
    neighbors = engine.find_neighbors_3d(elements_3d[0], elements_3d, radius=0.15)
    assert len(neighbors) == 1
    assert neighbors[0].element_id == "e2"

    # connections
    conns = engine.build_connections(elements_3d, same_page=True)
    # e1 and e2 connect same page, e1 and e3 connect next page
    assert len(conns) > 0
    edge_types = [c.edge_type for c in conns]
    assert "spatial_proximity" in edge_types
    assert "next_page" in edge_types


def test_field_and_statistics():
    """Test information field calculations and stats."""
    engine = Geometry3DEngine()
    elements_3d = [
        Element3D("e1", ElementType.TEXT, 0.5, 0.5, 0.0, 0.1, 0.1, 0.1, importance=1.0, page=1),
    ]

    # field value at center vs far away
    val_center = engine.compute_field_3d((0.5, 0.5, 0.0), elements_3d)
    val_far = engine.compute_field_3d((0.9, 0.9, 0.9), elements_3d)
    assert val_center > val_far

    # stats
    stats = engine.statistics(elements_3d)
    assert stats["n_elements"] == 1
    assert stats["n_pages"] == 1
    assert stats["mean_importance"] == 1.0

    # heatmaps
    grid_x, grid_y, heatmap = engine.field_heatmap_3d(elements_3d, plane="xy", resolution=10)
    assert grid_x.shape == (10, 10)
    assert heatmap.shape == (10, 10)


def test_visualization_plotly():
    """Test Plotly figure generation from 3D visualizer."""
    viz = Visualization3D()
    elements_3d = [
        Element3D("e1", ElementType.TEXT, 0.5, 0.5, 0.0, 0.1, 0.1, 0.1, importance=1.0, page=1),
    ]
    conns = [
        Connection3D("e1", "e2", (0.5, 0.5, 0.0), (0.6, 0.6, 0.0))
    ]

    fig_scatter = viz.scatter_3d(elements_3d)
    fig_boxes = viz.boxes_3d(elements_3d)
    fig_graph = viz.graph_3d(elements_3d, conns)
    fig_planes = viz.stacked_pages_3d(elements_3d)
    
    grid_x = np.linspace(0, 1, 10)
    grid_y = np.linspace(0, 1, 10)
    heatmap = np.zeros((10, 10))
    fig_heatmap = viz.heatmap_slice_3d(grid_x, grid_y, heatmap, plane="xy")

    # If Plotly is installed, all these should return go.Figure objects
    from src.visualization.visualization_3d import PLOTLY_AVAILABLE
    if PLOTLY_AVAILABLE:
        import plotly.graph_objects as go
        assert isinstance(fig_scatter, go.Figure)
        assert isinstance(fig_boxes, go.Figure)
        assert isinstance(fig_graph, go.Figure)
        assert isinstance(fig_planes, go.Figure)
        assert isinstance(fig_heatmap, go.Figure)
