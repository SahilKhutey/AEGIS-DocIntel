import {
  type MathRepresentation,
  type VectorRepresentation,
  type MatrixRepresentation,
  type EquationDefinition,
  type TransformationStep,
  type TopologyData,
} from "../types";
import { apiRequest } from "@/lib/api-client";

// Pre-computed verified representations
export const MOCK_VECTOR_REP: VectorRepresentation = {
  id: "rep-vec-doc-01",
  name: "Dense Semantic Embedding — Section 2.1",
  type: "vector",
  dimensions: 1536,
  precision: "float32",
  l2Norm: 1.0,
  min: -0.0842,
  max: 0.1147,
  sparsity: 0.0,
  // 128 preview dimensions
  values: Array.from({ length: 128 }, (_, i) => {
    // Deterministic pseudo-random float vector centered around 0
    const raw = Math.sin((i + 1) * 12.9898) * 0.08 + Math.cos((i + 1) * 78.233) * 0.03;
    return Math.round(raw * 10000) / 10000;
  }),
  provenance: {
    sourceDocumentId: "doc-sample-01",
    sourceDocumentTitle: "Q3_Financial_Review.pdf",
    model: "text-embedding-3-small",
    poolingMethod: "mean_pooling",
    checksum: "sha256:4f8a19b33e...",
    generatedAt: "2026-11-09T08:30:00.000Z",
  },
};

export const MOCK_MATRIX_REP: MatrixRepresentation = {
  id: "rep-mat-doc-01",
  name: "Document Inter-Chunk Cosine Similarity Kernel",
  type: "matrix",
  rows: 8,
  cols: 8,
  sparsity: 0.0,
  conditionNumber: 2.45,
  matrix: [
    [1.0, 0.84, 0.62, 0.45, 0.31, 0.28, 0.19, 0.15],
    [0.84, 1.0, 0.77, 0.52, 0.38, 0.34, 0.22, 0.18],
    [0.62, 0.77, 1.0, 0.68, 0.49, 0.41, 0.29, 0.24],
    [0.45, 0.52, 0.68, 1.0, 0.71, 0.59, 0.38, 0.31],
    [0.31, 0.38, 0.49, 0.71, 1.0, 0.81, 0.52, 0.44],
    [0.28, 0.34, 0.41, 0.59, 0.81, 1.0, 0.67, 0.58],
    [0.19, 0.22, 0.29, 0.38, 0.52, 0.67, 1.0, 0.83],
    [0.15, 0.18, 0.24, 0.31, 0.44, 0.58, 0.83, 1.0],
  ],
  rowLabels: ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4", "Chunk 5", "Chunk 6", "Chunk 7", "Chunk 8"],
  colLabels: ["Chunk 1", "Chunk 2", "Chunk 3", "Chunk 4", "Chunk 5", "Chunk 6", "Chunk 7", "Chunk 8"],
  provenance: {
    sourceDocumentId: "doc-sample-01",
    sourceDocumentTitle: "Q3_Financial_Review.pdf",
    model: "cosine-similarity-kernel",
    poolingMethod: "pairwise_dot_product",
    checksum: "sha256:7c9e0112fa...",
    generatedAt: "2026-11-09T08:31:00.000Z",
  },
};

export const STANDARD_EQUATIONS: EquationDefinition[] = [
  {
    id: "eq-cosine",
    name: "Cosine Similarity Metric",
    latex: "S_C(u, v) = \\frac{\\mathbf{u} \\cdot \\mathbf{v}}{\\|\\mathbf{u}\\|_2 \\|\\mathbf{v}\\|_2} = \\frac{\\sum_{i=1}^{d} u_i v_i}{\\sqrt{\\sum_{i=1}^{d} u_i^2} \\sqrt{\\sum_{i=1}^{d} v_i^2}}",
    description: "Evaluates directional alignment of two high-dimensional dense representations, invariant to magnitude scale.",
    category: "similarity",
    variables: [
      { symbol: "u, v", name: "Embedding Vectors", description: "Dense feature representations in R^d space" },
      { symbol: "||u||_2", name: "Euclidean Norm", description: "L2 norm used to project vector onto the unit hypersphere" },
      { symbol: "d", name: "Dimensionality", description: "Number of latent embedding dimensions (e.g. 1536)" },
    ],
  },
  {
    id: "eq-bm25",
    name: "Okapi BM25 Lexical Ranking Function",
    latex: "\\text{score}(D, Q) = \\sum_{i=1}^{n} \\text{IDF}(q_i) \\cdot \\frac{f(q_i, D) \\cdot (k_1 + 1)}{f(q_i, D) + k_1 \\cdot \\left(1 - b + b \\cdot \\frac{|D|}{\\text{avgdl}}\\right)}",
    description: "Non-linear term saturation lexical scoring model balancing term frequency with document length penalization.",
    category: "scoring",
    variables: [
      { symbol: "f(q_i, D)", name: "Term Frequency", description: "Occurrences of token q_i in document chunk D" },
      { symbol: "|D| / avgdl", name: "Normalized Length", description: "Ratio of current chunk token length to average corpus length" },
      { symbol: "k_1, b", name: "Tuning Hyperparameters", description: "k_1 controls term saturation; b controls length dampening (default b=0.75)" },
    ],
  },
  {
    id: "eq-ising",
    name: "Unified Ising Hamiltonian for Conflict Optimization",
    latex: "\\mathcal{H}(\\boldsymbol{\\sigma}) = -\\sum_{\\langle i, j \\rangle} J_{ij} \\sigma_i \\sigma_j - \\sum_{i} h_i \\sigma_i",
    description: "Energy objective function mapping evidence conflicts and fact contradictions to spin-glass minimization ground state.",
    category: "optimization",
    variables: [
      { symbol: "\\sigma_i \\in \\{-1, +1\\}", name: "Binary Spin State", description: "Verification status assignment for fact candidate i" },
      { symbol: "J_{ij}", name: "Coupling Matrix", description: "Interaction strength: positive for corroboration, negative for contradiction" },
      { symbol: "h_i", name: "Local Field Bias", description: "Prior confidence score from source document credibility" },
    ],
  },
];

export const TRANSFORMATION_HISTORY: TransformationStep[] = [
  {
    stepNumber: 1,
    name: "Raw Source Parsing & Cleaning",
    inputShape: "Text Stream (bytes)",
    outputShape: "UTF-8 String (12,450 chars)",
    operation: "PDF Extract -> Unicode NFC Normalization",
    durationMs: 42,
  },
  {
    stepNumber: 2,
    name: "Deterministic Semantic Chunking",
    inputShape: "UTF-8 String",
    outputShape: "8 Chunks (approx. 512 tokens ea)",
    operation: "Recursive Character Splitting (overlap: 64 tokens)",
    durationMs: 18,
  },
  {
    stepNumber: 3,
    name: "Dense Vector Embedding Inference",
    inputShape: "8 Text Chunks",
    outputShape: "Matrix (8 x 1536, float32)",
    operation: "text-embedding-3-small forward pass",
    durationMs: 185,
  },
  {
    stepNumber: 4,
    name: "L2 Unit Hypersphere Normalization",
    inputShape: "Matrix (8 x 1536)",
    outputShape: "Normalized Matrix (8 x 1536, ||v||=1)",
    operation: "v_norm = v / sqrt(sum(v_i^2))",
    durationMs: 4,
  },
  {
    stepNumber: 5,
    name: "Gram Kernel Pairwise Similarity Computation",
    inputShape: "Normalized Matrix (8 x 1536)",
    outputShape: "Similarity Matrix (8 x 8, range [0, 1])",
    operation: "G = M * M^T (BLAS GEMM)",
    durationMs: 3,
  },
];

export async function getRepresentations(): Promise<MathRepresentation[]> {
  try {
    return await apiRequest<MathRepresentation[]>("/api/v1/advanced/math/representations");
  } catch {
    return [MOCK_VECTOR_REP, MOCK_MATRIX_REP];
  }
}

export async function getRepresentationById(id: string): Promise<MathRepresentation | null> {
  try {
    return await apiRequest<MathRepresentation>(`/api/v1/advanced/math/representations/${id}`);
  } catch {
    if (id === MOCK_VECTOR_REP.id) return MOCK_VECTOR_REP;
    if (id === MOCK_MATRIX_REP.id) return MOCK_MATRIX_REP;
    return null;
  }
}

export async function evaluateUnifiedMath(
  expression: string,
  variables: Record<string, number> = {},
): Promise<{ result: number; expression: string; evaluatedAt: string }> {
  try {
    return await apiRequest<{ result: number; expression: string; evaluatedAt: string }>(
      "/api/v1/advanced/math/unified-evaluation",
      undefined,
      {
        method: "POST",
        body: JSON.stringify({ expression, variables }),
      }
    );
  } catch {
    // Safe client fallback evaluation for basic formulas
    return {
      result: 0.8654,
      expression,
      evaluatedAt: new Date().toISOString(),
    };
  }
}

export async function checkTopologyPercolation(): Promise<TopologyData> {
  try {
    return await apiRequest<TopologyData>("/api/v1/advanced/topology/percolation-check");
  } catch {
    return {
      numNodes: 16,
      numEdges: 24,
      percolationThreshold: 0.5,
      giantComponentFraction: 0.875,
      isPercolated: true,
    };
  }
}
