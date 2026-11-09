# 02 — Information Architecture & Navigation

## 1. Route Register
The Intelligence Workspace introduces and refines 6 dedicated product routes:

| Route | Primary Component | Responsibility | Access Permission | Status |
|---|---|---|---|---|
| `/intelligence` | `IntelligenceHubPage` | Central operational landing page for intelligence capabilities | `workspace.read` | Operational |
| `/ask` | `AskPage` | Natural-language query interface with conversational history & evidence | `intelligence.query` | Operational |
| `/intelligence/retrieval` | `RetrievalPage` | Raw passage retrieval and ranking score inspector | `intelligence.query` | Operational |
| `/intelligence/evidence` | `EvidencePage` | Verbatim passage explorer, coordinate references, and grounding | `evidence.read` | Operational |
| `/intelligence/knowledge` | `KnowledgePage` | Interactive entity-relationship graph & accessible tabular view | `intelligence.query` | Operational |
| `/compare` | `ComparePage` | Cross-document fact alignment, variance analysis & conflict flags | `documents.compare` | Operational |

## 2. Navigation & Breadcrumb Hierarchy
All intelligence routes inherit the standard AEGIS Application Shell:
- **Top Header**: Workspace switcher, global search, notifications, account menu.
- **Sidebar**:
  - `Workspace` -> `Overview (/)`
  - `Documents` -> `Document Library (/documents)`
  - `Intelligence` -> `Ask AEGIS (/ask)`, `Compare Documents (/compare)`
  - `Governance` -> `Review Queue (/reviews)`
- **Breadcrumbs**:
  - `Workspace > Intelligence > Ask AEGIS`
  - `Workspace > Intelligence > Compare documents`
  - `Workspace > Intelligence > Retrieval`
  - `Workspace > Intelligence > Evidence explorer`
  - `Workspace > Intelligence > Knowledge graph`

## 3. Responsive Page Layout Patterns
1. **Three-Panel Layout (Desktop - `/ask`)**:
   - Left Panel (25%): Document scope filters and conversation history.
   - Center Panel (50%): Question composer and grounded response cards.
   - Right Panel (25%): Persistent `EvidencePanel` showing verbatim quoted text.
2. **Split Workspace (Desktop - `/compare`)**:
   - Document selection matrix (min 2 documents required).
   - Summary and difference cards.
   - Two-column alignment comparison table.
3. **Canvas + Inspector (Desktop - `/intelligence/knowledge`)**:
   - Controls & filter toolbar (node types, visual canvas vs accessible table view, zoom).
   - Interactive SVG canvas (75%).
   - Selected node metadata & edge inspector (25%).
4. **Stacked Mobile Layout**:
   - Collapses multi-column views into linear vertical streams with scrollable pill bars for scopes and filters.
