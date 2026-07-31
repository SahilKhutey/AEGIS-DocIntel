# AMDI-OS Fusion Engine

Multi-engine signal fusion: combines outputs from all 12 AMDI-OS engines (geometry, frequency, recurrence, matrix, template, semantic, graph, topology, spectral, tensor, information physics, retrieval) into a single ranked, confidence-scored context for AI agents.

## Mathematical Foundation

### Fusion Score
The unified scoring combines multi-engine weighted scores, confidence weighting, and position priors:
\[F(v) = \left( \sum_{i} w_i \cdot \text{score}_i(v) \right) \cdot C(v) \cdot P(v)\]
where:
* \(w_i\): Engine weights
* \(\text{score}_i\): Per-element score from engine \(i\)
* \(C(v)\): Confidence estimate
* \(P(v)\): Position prior (exponential decay based on layout position)

### Dynamic Weight Updates
Engine weights are dynamically adjusted based on performance and gradients:
\[w_i(t+1) = \text{Softmax}\left(\frac{w_i(t) + \eta \cdot \nabla_{w_i} L(w)}{\tau}\right)\]

### Confidence Estimation
Composite confidence evaluates inter-engine agreement and system constraints:
\[C(v) = w_{\text{agr}} \cdot \text{Agreement}(v) + w_{\text{ev}} \cdot \text{EV} + w_{\text{cons}} \cdot \text{CS} + w_{\text{pers}} \cdot \text{PS}\]
where:
* \(\text{Agreement}(v)\): Normalized standard deviation among engine predictions.
* \(\text{EV}\): Explained variance from matrix/tensor decompositions.
* \(\text{CS}\): Information-physics conservation score.
* \(\text{PS}\): Topological persistence lifetime strength.

## Directory Structure

* `__init__.py`: Package-level exposure.
* `fusion_engine.py`: Main orchestrator coordinating ranking, confidence, and fusion scoring.
* `dynamic_weighting.py`: Learns and dynamically shifts weights per engine based on performance.
* `ranking.py`: Fuses lists utilizing Weighted Sum, Reciprocal Rank Fusion (RRF), Borda count, and Condorcet voting.
* `confidence.py`: Estimates composite confidence from consensus, explained variance, conservation, and topology metrics.
* `fusion_scoring.py`: Computes unified score combining weights, confidence, and layout position priors.
* `weight_optimizer.py`: Optimizes engine weights against validation feedback using Gradient Ascent, Coordinate Descent, or Bandit methods.
* `score_calculator.py`: Core reduction formulas (Linear, Geometric, Harmonic, Max, Min).
* `fusion_manager.py`: Manages the state machine (Init → Ingest → Fuse → Optimize → Export).
* `exceptions.py`: Custom fusion-related exceptions.
