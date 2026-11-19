# AEGIS-DocIntel — GitHub Project Structure & Configuration Guide

This document defines the configuration, taxonomy, rulesets, and project board architecture for managing the Product Hunt launch programme in GitHub.

---

## 1. GitHub Project Board Specification

### Name
`AEGIS-DocIntel — Product Hunt Launch Control Center`

### Workflow Columns

| Column # | Column Name | Definition & Entry Criteria | Exit Criteria |
| :---: | :--- | :--- | :--- |
| **1** | **Backlog** | Approved tasks not yet scheduled for active sprint | Prioritized and dependencies identified |
| **2** | **Ready** | Dependencies resolved, prerequisites satisfied, unblocked | Developer or owner assigns themselves |
| **3** | **In Progress** | Active development, testing, drafting, or asset creation | Draft pull request or deliverable generated |
| **4** | **In Review** | Pull request open, technical or copy review underway | PR approved or revision requested |
| **5** | **Verification** | Automated CI suite passing, manual testing or audit running | Concrete evidence URL / log recorded |
| **6** | **Blocked** | Impeded by upstream dependency, external review, or defect | Blocker resolved |
| **7** | **Done** | Definition of Done satisfied and verified with proof | Closed and recorded |

### Custom Fields

| Field Name | Type | Options / Format | Description |
| :--- | :--- | :--- | :--- |
| **Priority** | Single Select | `P0 (Blocker)`, `P1 (Critical)`, `P2 (Enhancement)` | Launch impact level |
| **Workstream** | Single Select | `Product`, `Engineering`, `Security`, `Marketing`, `Release`, `Operations` | Functional discipline |
| **Owner** | Assignee | `@SahilKhutey` | Primary accountable individual |
| **Target Milestone** | Single Select | `PH-01`, `PH-02`, `PH-03`, `PH-04`, `PH-05`, `PH-06` | Associated release milestone |
| **Dependency** | Text | e.g. `PH-001`, `PH-044` | Prerequisites required before starting |
| **Verification Status** | Single Select | `Not Started`, `Pending Tests`, `Verified Green`, `Failed` | Audit & testing state |
| **Evidence URL** | URL / Text | Link to workflow run, test report, or signed charter | Proof of completion |
| **Launch Blocker** | Single Select | `Yes`, `No` | Prevents publication if unverified |

---

## 2. GitHub Milestones

1. **`PH-01 — Product Readiness`**
   - Core document pipeline, parsing, chunking, retrieval, citation verification, and clean-user E2E workflow.
2. **`PH-02 — Beta Validation`**
   - Security audit, tenant isolation, authentication, licensing, upload security, and closed beta evaluation.
3. **`PH-03 — Launch Website & Assets`**
   - Positioning, listing copy, FAQ, Maker comment, landing page, gallery, SVGs, and responsive design.
4. **`PH-04 — Release Candidate`**
   - Windows installer, portable package, release manifest, SBOM, Ed25519 signatures, clean installation, and signoff.
5. **`PH-05 — Product Hunt Launch`**
   - Manual maker submission, URL verification, rehearsal, launch date approval, and launch-day operations.
6. **`PH-06 — Post-Launch Stabilization`**
   - Funnel metrics, conversion analysis, user feedback triage, critical fixes, and retrospective.

---

## 3. GitHub Label Taxonomy

| Label | Color | Description |
| :--- | :--- | :--- |
| `launch` | `#0E8A16` | Scope of the Product Hunt launch programme |
| `launch:p0` | `#D93F0B` | Launch blocker — MUST be resolved before publication |
| `launch:p1` | `#FBCA04` | High priority — required for a strong and competitive launch |
| `launch:p2` | `#0075CA` | Post-launch improvement or nice-to-have |
| `area:product` | `#1D76DB` | Core product workflow and document intelligence |
| `area:backend` | `#5319E7` | Engine, API, parser, retrieval, vector search |
| `area:frontend` | `#1D76DB` | Next.js UI, web components, evaluation client |
| `area:security` | `#B60205` | Auth, licensing, encryption, tenant isolation |
| `area:release` | `#0052CC` | Distribution, packaging, installer, SBOM, signing |
| `area:marketing` | `#C5DEF5` | Copywriting, positioning, listing text, FAQ |
| `area:website` | `#BFDADC` | Public landing page, CTA, routing |
| `area:assets` | `#D4C5F9` | Screenshots, gallery, SVGs, logo, videos |
| `area:analytics` | `#006B75` | Telemetry, KPIs, metrics, conversion |
| `area:beta` | `#F9D0C4` | Beta onboarding, feedback, tester communications |
| `type:bug` | `#D73A4A` | Defect or software failure |
| `type:task` | `#A2EEEF` | Execution task or work item |
| `type:research` | `#D4C5F9` | User interviews, competitive research, market validation |
| `type:documentation` | `#0075CA` | Technical guides, release notes, user manuals |
| `status:blocked` | `#E11D21` | Impeded by upstream dependency or defect |
| `status:needs-verification` | `#E99695` | Awaiting automated test results or signoff |

---

## 4. Branch Rulesets & Protection

### Target Branch: `main` (and `master`)
- **Require a pull request before merging**: Enforced.
- **Require status checks to pass**:
  - `Required CI gate` (validates `backend`, `frontend`, and `integration`)
  - `CodeQL Security Scanning`
  - `Gitleaks History & Workspace Scan`
  - `Dependency & License Compliance Review`
- **Require linear history**: Enabled.
- **Require conversation resolution**: All PR comments resolved.
- **Block force pushes**: Enforced.
- **Block branch deletion**: Enforced.
- **Full-length SHA Pinning**: Enforced for all actions in `.github/workflows/`.

---

## 5. GitHub Environments & Secret Management

| Environment | Purpose | Protection Rule | Secrets Permitted |
| :--- | :--- | :--- | :--- |
| `ci` | Automated tests & quality | Open to PRs | No deployment secrets |
| `preview` | Marketing preview deployment | Automated on PR | `PREVIEW_DEPLOY_TOKEN` |
| `production` | Public landing page | Manual Maintainer Approval | `PRODUCTION_DEPLOY_TOKEN` |
| `release-signing` | Ed25519 signature & attestation | Restricted to release tags | Signing keys (OIDC / HSM) |
| `production-release` | GitHub Release publication | Manual Approval | `GITHUB_TOKEN` |

---

## 6. Seven Launch Readiness Gates

1. **Product Gate**: Ingestion, OCR/text extraction, parsing, chunking, retrieval, LLM orchestration, and citation verification pass on real files.
2. **Quality Gate**: 100% test pass rate across unit, integration, and regression suites; coverage thresholds met.
3. **Security Gate**: Zero secrets in repo/history; zero private backend exposure in client; tenant isolation verified; dependencies audited.
4. **Beta Gate**: Closed beta cohort successfully installed, activated, and evaluated without unhandled blockers.
5. **Website Gate**: Responsive landing page, clear value proposition, functional download CTA, and working links verified.
6. **Release Gate**: Signed Windows setup executable, portable ZIP, manifest, CycloneDX SBOM, and SLSA provenance verified.
7. **Launch Gate**: Formal GO decision approved; personal maker account ready; Product Hunt listing draft and Maker comment validated.
