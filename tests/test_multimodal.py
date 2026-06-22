import os
import sys
from pathlib import Path
import numpy as np
import pytest

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.multimodal import (
    MultiModalEngine,
    Modality,
    CLIPEmbedder,
    EnhancedTableExtractor,
    TableStructure,
    TableCell,
    CellType,
    ChartUnderstander,
    ChartType,
    ChartData,
    CaptionGenerator,
    CaptionStyle,
)


def test_image_embedder_fallback():
    embedder = CLIPEmbedder(embedding_dim=512)
    assert embedder.embedding_dim == 512

    # Test fallback image embedding
    dummy_img = b"random_image_bytes_here"
    vector = embedder.embed(dummy_img)
    assert vector is not None
    assert len(vector) == 512
    # Verify vector is normalized (norm close to 1.0)
    assert abs(np.linalg.norm(vector) - 1.0) < 1e-5

    # Test fallback text embedding
    text_vector = embedder.embed_text("sample text query")
    assert text_vector is not None
    assert len(text_vector) == 512
    assert abs(np.linalg.norm(text_vector) - 1.0) < 1e-5


def test_table_extractor():
    extractor = EnhancedTableExtractor(detect_headers=True)

    # Simple numeric table
    raw_data = [
        ["Quarter", "Revenue", "Growth"],
        ["Q1", "$10,000", "5.2%"],
        ["Q2", "$12,500", "25%"],
        ["Q3", "invalid", "10%"]
    ]

    structure = extractor.extract(raw_data)
    assert structure.headers == ["Quarter", "Revenue", "Growth"]
    assert structure.row_count == 3
    assert structure.col_count == 3
    assert structure.completeness > 0.8

    # Test get numeric column
    rev_col = structure.get_numeric_column(1)
    assert rev_col == [10000.0, 12500.0, None]

    growth_col = structure.get_numeric_column(2)
    assert growth_col == [5.2, 25.0, 10.0]

    # Test column types detection
    col_types = extractor.detect_column_types(structure)
    assert col_types[0] == "text"
    assert col_types[1] == "numeric"


def test_chart_understander():
    understander = ChartUnderstander()

    # Create dummy square image bytes for PIE heuristic
    # (Since Pillow might fail to read invalid image bytes, we catch exception)
    import io
    from PIL import Image
    
    img = Image.new("RGB", (100, 100))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    square_bytes = img_byte_arr.getvalue()

    chart_data = understander.understand(square_bytes)
    assert chart_data.chart_type == ChartType.PIE
    assert chart_data.confidence > 0.0

    # Test anomaly detection
    series = {
        "name": "sales",
        "points": [
            {"x": 1, "y": 10.0},
            {"x": 2, "y": 12.0},
            {"x": 3, "y": 110.0},  # outlier
            {"x": 4, "y": 9.0},
            {"x": 5, "y": 11.0},
            {"x": 6, "y": 10.0},
            {"x": 7, "y": 12.0},
            {"x": 8, "y": 9.0},
            {"x": 9, "y": 11.0},
            {"x": 10, "y": 10.0},
            {"x": 11, "y": 12.0},
            {"x": 12, "y": 9.0},
            {"x": 13, "y": 11.0},
            {"x": 14, "y": 10.0},
            {"x": 15, "y": 12.0},
        ]
    }
    chart_data.series = [series]
    anomalies = understander.detect_anomalies(chart_data)
    assert len(anomalies) == 1
    assert anomalies[0]["index"] == 2
    assert anomalies[0]["value"] == 110.0


def test_caption_generator():
    generator = CaptionGenerator()
    
    # Image captioning
    caption = generator.generate(b"img_bytes", style=CaptionStyle.CONCISE)
    assert "image" in caption.lower()

    # Table captioning
    table = TableStructure(
        headers=["Month", "Volume"],
        rows=[["Jan", "50"], ["Feb", "60"]],
        row_count=2,
        col_count=2,
        completeness=1.0
    )
    table_caption = generator.generate_table_caption(table)
    assert "table" in table_caption.lower()
    assert "2 rows" in table_caption
    assert "Month" in table_caption

    # Chart captioning
    chart = ChartData(
        chart_type=ChartType.BAR,
        title="Revenue over Time",
        x_label="Quarter",
        y_label="USD",
        confidence=0.9
    )
    chart_caption = generator.generate_chart_caption(chart)
    assert "revenue over time" in chart_caption.lower()
    assert "bar chart" in chart_caption.lower()


def test_multimodal_engine_integration():
    engine = MultiModalEngine()

    # Process image
    img_res = engine.process_image(
        document_id="doc_1",
        image_data=b"img_bytes",
        image_format="jpeg",
        generate_caption=True
    )
    assert img_res.modality == Modality.IMAGE
    assert img_res.embedding is not None
    assert img_res.caption is not None

    # Process table
    table_res = engine.process_table(
        document_id="doc_1",
        table_data=[["Name", "Score"], ["Alice", "95"]]
    )
    assert table_res.modality == Modality.TABLE
    assert "Alice" in table_res.data["structure"]["rows"][0]

    # Cross-modal search (using dummy data)
    images = [b"img_a", b"img_b", b"img_c"]
    search_results = engine.cross_modal_search("find a dog", images, top_k=2)
    assert len(search_results) == 2
    assert search_results[0].modality == Modality.IMAGE
