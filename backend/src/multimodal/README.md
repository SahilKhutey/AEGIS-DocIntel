# Multi-Modal Support

## Capabilities

| Component | Description |
|-----------|-------------|
| `image_embedder.py` | CLIP-based image + text embeddings |
| `table_extractor.py` | Enhanced table extraction + type detection |
| `chart_understander.py` | Chart type detection + data extraction |
| `caption_generator.py` | Figure/table/chart caption generation |
| `multimodal_engine.py` | Main orchestrator |

## Usage

```python
from backend.src.multimodal import MultiModalEngine, Modality

engine = MultiModalEngine()

# Process image
result = engine.process_image(
    document_id="doc_001",
    image_data=image_bytes,
    generate_caption=True,
)
print(result.caption)

# Process table
result = engine.process_table(
    document_id="doc_001",
    table_data=[["Method", "Accuracy"], ["AMDI-OS", "94%"]],
)
print(result.caption)

# Cross-modal search
results = engine.cross_modal_search(
    query="quantum mechanics diagram",
    images=[img1_bytes, img2_bytes, img3_bytes],
    top_k=5,
)
```

## Dependencies
- `transformers` (HuggingFace CLIP)
- `Pillow`
- `torch` (for CLIP)
