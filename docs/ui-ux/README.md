# AEGIS-DocIntel — UI/UX Enterprise Workbench Architecture & Dossier

| Field | Value |
| :--- | :--- |
| **Product** | AEGIS-DocIntel Enterprise Document Intelligence Workbench |
| **Frontend Framework** | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS |
| **Backend API** | FastAPI, Python 3.12, SQLite WAL Transactional Engine |
| **Release Status** | Validated & Released (GO Verdict) |
| **Accessibility** | 100% WCAG 2.2 Level AA Compliant (axe-core verified) |
| **Automated Testing** | 46 Vitest Suites (220 tests), 87 Playwright E2E Tests |

---

## 1. Overview & Vision

The AEGIS-DocIntel UI/UX Workstream transforms the platform into an enterprise-grade document intelligence workbench with grounded citations, human-in-the-loop governance, and mathematical observability.

The design and engineering of every screen adhere to the core platform axiom:
> **"AI produces intelligence; evidence supports verification; authorized humans make governance decisions."**

The workbench eliminates ungrounded conversational hallucinations by strictly tying every natural-language answer to verbatim source spans, spatial bounding boxes, and document page references.

---

## 2. Work Package Inventory

The frontend architecture is organized into 8 interconnected work packages:

```
docs/ui-ux/
├── README.md                                 # Master UI/UX architecture index (this document)
├── DEVLOG.md                                 # UI/UX engineering development narrative
├── TASKLOG.md                                # Chronological task execution and quality gate log
├── wp-ui-01-product-ux-architecture/         # Persona models, RBAC mapping, 30-route register
├── wp-ui-02-design-system/                   # Semantic token engine, WCAG 2.2 AA components
├── wp-ui-03-application-shell/               # Collapsible sidebar, header, global Ctrl+K search
├── wp-ui-04-core-workspace/                  # Document ingestion, library table, inspector, queue
├── wp-ui-05-intelligence-workspace/          # Grounded Q&A, citations, comparison diffing
├── wp-ui-06-governance-workspace/            # Human review queue, fact verification, audit trail
├── wp-ui-07-advanced-interfaces/             # Analytics, KaTeX math, DAG visualizer, SLA telemetry
└── wp-ui-08-integration-ux-validation/       # System integration, E2E browser tests, release audit
```

### Detailed Work Package Specifications

| Work Package | Deliverable Focus | Key Components & Routes | Documentation |
| :--- | :--- | :--- | :--- |
| **WP-UI-01** | **Product UX Architecture** | 5 Personas, Backend RBAC Mapping, 30-Route Registry | [`wp-ui-01-product-ux-architecture/README.md`](wp-ui-01-product-ux-architecture/README.md) |
| **WP-UI-02** | **Design System** | Semantic Tokens, Typography, Contrast Ratios (>=4.5:1) | [`wp-ui-02-design-system/README.md`](wp-ui-02-design-system/README.md) |
| **WP-UI-03** | **Application Shell** | Global Header, Collapsible Sidebar, `Ctrl+K` Search | [`wp-ui-03-application-shell/README.md`](wp-ui-03-application-shell/README.md) |
| **WP-UI-04** | **Core Workspace** | Ingestion Modal, Document Library, Inspector, Monitor | [`wp-ui-04-core-workspace/README.md`](wp-ui-04-core-workspace/README.md) |
| **WP-UI-05** | **Intelligence Workspace** | Ask AEGIS Grounded Q&A, Citation Drawer, Document Compare | [`wp-ui-05-intelligence-workspace/README.md`](wp-ui-05-intelligence-workspace/README.md) |
| **WP-UI-06** | **Governance Workspace** | Human Review Queue, Fact Verification, Immutable Audit | [`wp-ui-06-governance-workspace/README.md`](wp-ui-06-governance-workspace/README.md) |
| **WP-UI-07** | **Advanced Interfaces** | Analytics CSV Export, KaTeX Math, Pipeline DAG, SLA Gauges | [`wp-ui-07-advanced-interfaces/README.md`](wp-ui-07-advanced-interfaces/README.md) |
| **WP-UI-08** | **Integration & Validation** | Unified API Client, Playwright E2E, WCAG AA Certification | [`wp-ui-08-integration-ux-validation/README.md`](wp-ui-08-integration-ux-validation/README.md) |

---

## 3. Running & Testing the Web Workbench

The frontend codebase is located under [`web/`](../../web/):

```bash
cd web

# 1. Install dependencies
npm install

# 2. Run local development server
npm run dev

# 3. Run unit and component test suite (Vitest: 46 suites, 220 tests)
npm run test

# 4. Run end-to-end browser regression suite (Playwright: 87 tests)
npm run test:e2e

# 5. Typecheck and linting
npx tsc --noEmit
npm run lint

# 6. Production Turbopack compilation
npm run build
```

---

## 4. Verification Evidence & Quality Gates

All release gates have been validated with zero defect tolerance:

- **Vitest Unit/Component Tests**: 46 / 46 suites passed (220 tests passed, 100%).
- **Playwright E2E Tests**: 87 / 87 browser tests passed (100%).
- **Accessibility Certification**: 12 / 12 routes scanned with axe-core (0 critical, 0 serious violations).
- **Responsive Fluidity**: 60 / 60 viewports verified across 6 standard viewports (375px to 1920px) with 0 horizontal overflow.
- **Static Code Quality**: ESLint (0 errors, 0 warnings), TypeScript (0 type errors).
- **Production Compilation**: Next.js Turbopack compiled all 30 routes cleanly with 0 prerender warnings.

Full raw execution logs are archived under [`wp-ui-08-integration-ux-validation/evidence/`](wp-ui-08-integration-ux-validation/evidence/).
