# 06 — Knowledge Visualization Specification

## 1. Functional Scope
The Knowledge Visualization interface (`/intelligence/knowledge`) renders structured entity and relationship graphs derived from extracted facts across documents.
Key features:
1. **Interactive Visual Canvas**: SVG-based force/circular graph layout with color-coded nodes (entities, documents, concepts) and directed relationship edges.
2. **Interactive Node Selection**: Clicking any node highlights connected edges and populates a detailed metadata sidebar.
3. **Type Filtering**: Allows filtering nodes by category (`all`, `entity`, `document`, `concept`).
4. **Canvas Controls**: Zoom in, zoom out, reset view.
5. **Accessible Tabular Alternative (WCAG 2.2 AA)**: Seamless toggle to a semantic table listing all nodes, types, identifiers, and connected relationships.

## 2. Graph Data Model
- **KnowledgeNode**:
  - `id`: Unique identifier (e.g., `doc-1`, `entity-acme-corp`).
  - `label`: Human-readable name.
  - `type`: Category (`document`, `entity`, `concept`).
  - `documentIds`: Provenance document IDs.
- **KnowledgeEdge**:
  - `id`: Edge identifier.
  - `source`: Source node ID.
  - `target`: Target node ID.
  - `relationship`: Predicate / extracted attribute value.

## 3. Component Architecture
```
web/src/features/intelligence/
├── api/
│   └── knowledge.api.ts        # POST /api/v1/intelligence/graph with fallback to document facts
└── components/
    └── KnowledgeGraph.tsx      # SVG canvas, controls, node sidebar, and accessible table view
```
