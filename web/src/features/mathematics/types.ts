export type MathRepresentationType = "vector" | "matrix" | "formula" | "topology";

export interface RepresentationProvenance {
  sourceDocumentId: string;
  sourceDocumentTitle: string;
  model: string;
  poolingMethod: string;
  checksum: string;
  generatedAt: string;
}

export interface VectorRepresentation {
  id: string;
  name: string;
  type: "vector";
  dimensions: number;
  precision: "float32" | "float64";
  l2Norm: number;
  min: number;
  max: number;
  sparsity: number; // percentage of 0s
  values: number[]; // can contain first chunk (e.g. 128 elements) or full vector
  provenance: RepresentationProvenance;
}

export interface MatrixRepresentation {
  id: string;
  name: string;
  type: "matrix";
  rows: number;
  cols: number;
  sparsity: number;
  conditionNumber?: number;
  matrix: number[][];
  rowLabels?: string[];
  colLabels?: string[];
  provenance: RepresentationProvenance;
}

export interface EquationVariable {
  symbol: string;
  name: string;
  description: string;
}

export interface EquationDefinition {
  id: string;
  name: string;
  latex: string;
  description: string;
  category: "similarity" | "scoring" | "optimization" | "topology";
  variables: EquationVariable[];
}

export interface TransformationStep {
  stepNumber: number;
  name: string;
  inputShape: string;
  outputShape: string;
  operation: string;
  durationMs: number;
}

export interface TopologyData {
  numNodes: number;
  numEdges: number;
  percolationThreshold: number;
  giantComponentFraction: number;
  isPercolated: boolean;
}

export type MathRepresentation = VectorRepresentation | MatrixRepresentation;
