# AMDI-OS Advanced Analytics Module

Enterprise analytical engine providing document similarity searching, relationship graph construction, trend forecasting, user behavior metrics, and cost optimization recommendations.

---

## Mathematical Formulations

### 1. Document Similarity (Cosine Similarity)
Calculates the angular difference between two embedding vectors in space:
$$\text{similarity}(\mathbf{v}_1, \mathbf{v}_2) = \frac{\mathbf{v}_1 \cdot \mathbf{v}_2}{\|\mathbf{v}_1\|_2 \|\mathbf{v}_2\|_2} = \frac{\sum_{i=1}^{d} v_{1,i} v_{2,i}}{\sqrt{\sum_{i=1}^{d} v_{1,i}^2} \sqrt{\sum_{i=1}^{d} v_{2,i}^2}}$$

### 2. Timeseries Trend Line (Least Squares Linear Regression)
Fits a linear equation $y = mx + c$ by minimizing the sum of squared residuals:
$$m = \frac{N \sum (xy) - \sum x \sum y}{N \sum (x^2) - (\sum x)^2}$$
$$c = \frac{\sum y - m \sum x}{N}$$

### 3. Mean Reciprocal Rank (MRR)
Measures search quality by averaging the reciprocal rank of the first relevant result:
$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$

---

## Code Example

```python
from backend.src.analytics import AnalyticsEngine

# Initialize the engine
engine = AnalyticsEngine()

# Add document embeddings
engine.similarity_searcher.add_document("doc_1", [0.1, 0.9, 0.0], {"title": "Doc 1"})
engine.similarity_searcher.add_document("doc_2", [0.15, 0.85, 0.05], {"title": "Doc 2"})

# Perform similarity search
results = engine.similarity_searcher.search_by_document("doc_1", top_k=1)
print(results)  # Finds doc_2

# Graph Generation
kg = engine.generate_similarity_knowledge_graph(similarity_threshold=0.8)
print(kg.to_visualization_json())
```
