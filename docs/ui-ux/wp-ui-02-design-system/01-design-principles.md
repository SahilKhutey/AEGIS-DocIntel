# 01 — Design Principles & Visual Direction

**Document Identifier**: `AEGIS-DOCINTEL-DS-001`  
**Work Package**: `WP-UI-02: Design System`  
**Status**: APPROVED BASELINE  
**Effective Date**: 2026-11-09  

---

## 1. Visual Identity & Workbench Philosophy

AEGIS-DocIntel is not an entertainment portal, a consumer social feed, or an ungrounded conversational toy. It is a high-assurance **Document Intelligence Workbench** designed for mission-critical document analysis, vector geometry inspections, topological graph comparisons, citation verification, and human governance.

The aesthetic direction is grounded in three core pillars:
$$\text{Precision} \quad\cdot\quad \text{Clarity} \quad\cdot\quad \text{Trust}$$

The interface combines high information density with deliberate visual breathing room. Every pixel, margin, and typography scale is engineered to minimize cognitive overhead when analysts evaluate complex enterprise contracts, regulatory disclosures, and multi-page technical documentation.

---

## 2. The Seven Governing Principles

### Principle 1: Information Density Without Visual Clutter
- **Policy**: Deep analytical workspaces require dense tables, multi-column evidence sidebars, and comprehensive metadata badges. Density must be achieved through structured tabular grids, clear column headers, and 4px baseline rhythm—not through tiny, unreadable fonts or overlapping panels.
- **Enforcement**: Minimum font size for metadata is 12px (`--text-xs`). All spacing scales follow strict 4px multiples (`--space-1` through `--space-16`). Arbitrary inline paddings are rejected in code review.

### Principle 2: Clear Hierarchy for Documents, Evidence, and Analytical Results
- **Policy**: When analyzing a document or querying intelligence, the user must instantly distinguish between:
  1. *Primary source material* (the ingested document extract or raw page view).
  2. *Intelligence derivations* (answers generated through retrieval and topological reasoning).
  3. *Verifiable grounding evidence* (exact quote, page number, bounding coordinates, and confidence score).
- **Enforcement**: Source materials are styled in neutral surface cards. Grounded citations carry dedicated evidence badges and click-to-highlight affordances. Derived intelligence is clearly segregated from immutable source citations.

### Principle 3: Consistent Status Communication Across Ingestion and Governance
- **Policy**: A document status or governance review decision must convey identical meaning across the entire application—whether on the dashboard card, the document library table, or the audit log.
- **Enforcement**: Status communication uses the standardized `StatusBadge` and `Alert` components. All status states map to centralized states (`pending`, `indexing`, `ready`, `failed`, `in_review`, `approved`, `corrected`, `rejected`, `needs_evidence`).

### Principle 4: Accessible Interaction and Complete Keyboard Operability
- **Policy**: Mouse-free interaction is an engineering requirement, not an optional bonus. An analyst or reviewer must be able to navigate the entire workspace, inspect evidence, trigger queries, and submit governance decisions using keyboard shortcuts and tab navigation alone.
- **Enforcement**:
  - Global `:focus-visible` ring with 3px high-contrast outline (`--primary`) and 2px offset.
  - Dedicated skip-link (`#main-content`) accessible on the first Tab keystroke.
  - Interactive components trap and restore focus appropriately (e.g., `<Dialog />`).

### Principle 5: Responsive Layouts Without Losing Critical Context
- **Policy**: Responsive design must never degrade document intelligence workflows by silently dropping or hiding critical data columns, evidence drawers, or comparison documents.
- **Enforcement**: Narrow viewports utilize prioritized horizontal scroll tables, tabbed comparison views, and collapsible drawers rather than truncating critical metadata.

### Principle 6: Reusable Primitives Over Page-Specific Styling
- **Policy**: Screen implementations must not introduce ad-hoc CSS classes, one-off color hex codes, or unvetted UI containers.
- **Enforcement**: Every button, card, input, dialog, and table must be composed directly from `@/components/ui/` primitives and styled with semantic design tokens.

### Principle 7: Zero Status Communicated by Color Alone
- **Policy**: Color must never serve as the sole channel for communicating critical operational status, validation errors, citation validity, or governance review outcomes.
- **Enforcement**: Every color-coded badge, alert, and indicator includes programmatic text labels, semantic icons, or dedicated ARIA attributes (`role="status"`, `role="alert"`).
