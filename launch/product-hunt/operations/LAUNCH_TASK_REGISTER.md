# AEGIS-DocIntel — Product Hunt Launch Task Register (PH-001 through PH-070)

This register defines the complete 70-task inventory required to launch AEGIS-DocIntel on Product Hunt as an authenticated, grounded document intelligence beta.

## Programme Structure & Milestone Mapping

| Milestone | Code | Scope | Primary Objective |
| :--- | :--- | :--- | :--- |
| **Milestone 1** | `PH-01` | Product Readiness | Restore & verify end-to-end document processing pipeline on real files |
| **Milestone 2** | `PH-02` | Beta Validation | Security boundary audit, tenant isolation, and closed beta onboarding |
| **Milestone 3** | `PH-03` | Launch Website & Assets | Positioning, marketing copy, landing page, and visual gallery assets |
| **Milestone 4** | `PH-04` | Release Candidate | Packaged Windows installer, portable ZIP, SBOM, Ed25519 signing & signoff |
| **Milestone 5** | `PH-05` | Product Hunt Launch | Manual maker submission, launch-day operations, monitoring & support |
| **Milestone 6** | `PH-06` | Post-Launch Stabilization | Funnel conversion analysis, feedback triage, and defect remediation |

---

## Phase A: Product Readiness (Milestone: PH-01)
> **Launch Principle**: A successful frontend build is NOT equivalent to product readiness. Document ingestion, parsing, chunking, retrieval, token budgets, and citations must work reliably on real files before launch.

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-001` | Audit current product functionality | Inspect actual frontend, backend, APIs, file pipeline, LLM and optimizer | Feature functionality matrix completed | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-002` | Fix document upload and file lifecycle | Validate upload, persistence, retrieval and deletion | End-to-end file tests pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-003` | Restore extraction pipeline | Verify supported PDF, DOCX and TXT extraction | Ground-truth extraction tests pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-004` | Restore document parsing | Validate structure, metadata, tables and page references | Parser fixtures pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-005` | Restore processing orchestration | Implement jobs, status, retry and error handling | Job lifecycle tests pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-006` | Restore retrieval and indexing | Validate chunking, indexing and evidence retrieval | Retrieval benchmark passes | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-007` | Restore context optimization | Implement token budgets and evidence selection | Token and context tests pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-008` | Validate LLM integration | Check provider configuration, execution, timeouts and errors | Real request and response tests pass | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-009` | Implement citation verification | Ensure answers refer to actual document locations | Citation test suite passes | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-010` | Complete primary user workflow | Connect frontend to the real processing pipeline | Clean-user E2E test passes | `launch:p0` | Engineering | `PH-01 — Product Readiness` |
| `PH-011` | Document known limitations | Identify unsupported features and file types | Public limitations document approved | `launch:p1` | Docs | `PH-01 — Product Readiness` |

---

## Phase B: Security, Privacy & Beta (Milestone: PH-02)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-012` | Complete authentication verification | Test login, session expiry and logout | Auth tests pass | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-013` | Complete activation and licensing | Verify activation, expiry, device limits and revocation | Licensing tests pass | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-014` | Verify entitlement and quota enforcement | Check protected features and usage limits | Negative authorization tests pass | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-015` | Verify tenant isolation | Test document and workspace access boundaries | Cross-tenant tests fail closed | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-016` | Complete upload security checks | Validate file types, size, malformed files and archive handling | Security tests pass | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-017` | Approve privacy and data handling | Document retention, LLM providers and deletion behavior | Disclosures and policies reviewed | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-018` | Complete security audit | Review client exposure, secrets, dependency risks and APIs | No unresolved critical/high blockers | `launch:p0` | Security | `PH-02 — Beta Validation` |
| `PH-019` | Create beta feedback process | Prepare issue form, severity labels and response procedure | Feedback intake tested | `launch:p0` | Operations | `PH-02 — Beta Validation` |
| `PH-020` | Run closed beta | Invite a small group and observe actual workflows | Findings and feedback report published | `launch:p0` | Operations | `PH-02 — Beta Validation` |
| `PH-021` | Resolve beta blockers | Fix defects discovered during evaluation | Critical beta defects closed or release blocked | `launch:p0` | Engineering | `PH-02 — Beta Validation` |

---

## Phase C: Positioning & Market Validation (Milestone: PH-03)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-022` | Finalize product positioning | Define product category, problem and value proposition | Positioning document approved | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-023` | Validate target users | Interview 5–10 relevant researchers or technical users | Interview findings documented | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-024` | Research competitors | Compare actual features, pricing, workflow and privacy | Evidence-backed comparison completed | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-025` | Select primary use case | Choose the strongest demonstrated workflow | Primary use case approved | `launch:p1` | Product | `PH-03 — Launch Website & Assets` |
| `PH-026` | Finalize product name | Confirm consistent AEGIS-DocIntel branding | Product naming consistent | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-027` | Finalize Product Hunt tagline | Describe the real product clearly | Tagline approved | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-028` | Finalize listing description | Describe actual shipped capabilities and limitations | Description verified against product | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-029` | Prepare Maker comment | Explain founder story, problem and request for feedback | Comment approved | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |
| `PH-030` | Prepare launch FAQ | Answer installation, privacy, features, pricing and support questions | FAQ reviewed | `launch:p1` | Marketing | `PH-03 — Launch Website & Assets` |

---

## Phase D: Website & Launch Assets (Milestone: PH-03)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-031` | Build Product Hunt landing page | Create focused public product page | Responsive production page deployed | `launch:p0` | Frontend | `PH-03 — Launch Website & Assets` |
| `PH-032` | Implement primary CTA | Connect visitors to the real evaluation or download path | CTA tested end-to-end | `launch:p0` | Frontend | `PH-03 — Launch Website & Assets` |
| `PH-033` | Implement signup and activation | Test new-user onboarding | Clean-user onboarding succeeds | `launch:p0` | Engineering | `PH-03 — Launch Website & Assets` |
| `PH-034` | Add product screenshots | Capture actual application workflows | Images accurately reflect the release | `launch:p0` | Assets | `PH-03 — Launch Website & Assets` |
| `PH-035` | Create product gallery | Prepare 3–5 informative images | Gallery reviewed | `launch:p0` | Assets | `PH-03 — Launch Website & Assets` |
| `PH-036` | Create logo and launch graphics | Prepare consistent brand assets | Assets approved | `launch:p0` | Assets | `PH-03 — Launch Website & Assets` |
| `PH-037` | Create demonstration video | Record an actual end-to-end product workflow | Video checked for accuracy | `launch:p1` | Assets | `PH-03 — Launch Website & Assets` |
| `PH-038` | Create architecture graphic | Explain the real product workflow | Diagram matches implementation | `launch:p1` | Assets | `PH-03 — Launch Website & Assets` |
| `PH-039` | Implement SEO and social metadata | Add title, description, Open Graph and social preview | Metadata validated | `launch:p1` | Frontend | `PH-03 — Launch Website & Assets` |
| `PH-040` | Verify website links | Test all CTA, privacy, support and documentation links | Link-check workflow passes | `launch:p0` | Operations | `PH-03 — Launch Website & Assets` |
| `PH-041` | Verify responsive layout | Test mobile, tablet and desktop | Layout checks pass | `launch:p0` | Frontend | `PH-03 — Launch Website & Assets` |
| `PH-042` | Add privacy and support information | Publish accurate policies and contact route | Pages available publicly | `launch:p0` | Docs | `PH-03 — Launch Website & Assets` |

---

## Phase E: Release Candidate (Milestone: PH-04)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-043` | Establish release commit | Select approved source commit | Commit SHA recorded | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-044` | Implement client packaging | Assemble allowlisted client package | Package inspection passes | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-045` | Build Windows installer | Create Windows x64 installer | Fresh installation succeeds | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-046` | Build portable package | Create portable ZIP | Portable launch succeeds | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-047` | Generate release manifest | Include version, source SHA, hashes and metadata | Manifest validated | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-048` | Generate client SBOM | Produce software bill of materials | SBOM generated and reviewed | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-049` | Sign release artifacts | Sign metadata and eligible executables | Signature verification passes | `launch:p0` | Security | `PH-04 — Release Candidate` |
| `PH-050` | Test clean installation | Test on clean Windows environment | No developer dependencies needed | `launch:p0` | Release | `PH-04 — Release Candidate` |
| `PH-051` | Test complete application workflow | Run document upload through verified answer | Full E2E passes | `launch:p0` | QA | `PH-04 — Release Candidate` |
| `PH-052` | Test update and uninstall | Validate upgrade, rollback strategy and uninstall | Installer tests pass | `launch:p0` | QA | `PH-04 — Release Candidate` |
| `PH-053` | Publish known limitations | Prepare release notes and limitations | Public documents approved | `launch:p0` | Docs | `PH-04 — Release Candidate` |
| `PH-054` | Complete release signoff | Review every P0 gate | Signed GO decision | `launch:p0` | Leadership | `PH-04 — Release Candidate` |

---

## Phase F: Product Hunt Submission & Launch (Milestone: PH-05)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-055` | Create personal Product Hunt maker account | Verify personal account and posting access | Account ready | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-056` | Create Product Hunt draft | Enter name, tagline, description and product URL | Draft saved | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-057` | Upload logo and gallery | Add approved assets | Preview reviewed | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-058` | Add launch tags and makers | Complete Product Hunt page details | Required submission fields complete | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-059` | Add Maker comment | Publish the prepared comment in draft | Comment reviewed | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-060` | Verify public product URL | Test product page and download path | External access works | `launch:p0` | Operations | `PH-05 — Product Hunt Launch` |
| `PH-061` | Final launch rehearsal | Run installation, signup, activation and document workflow | Rehearsal passes | `launch:p0` | QA | `PH-05 — Product Hunt Launch` |
| `PH-062` | Approve launch date | Review readiness and schedule | Formal GO decision | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-063` | Publish Product Hunt launch | Submit from personal maker account | Product listing is live | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |
| `PH-064` | Monitor launch day | Respond to comments, monitor failures and support users | Coverage and incident log maintained | `launch:p0` | **Manual** | `PH-05 — Product Hunt Launch` |

---

## Phase G: Post-Launch Stabilization (Milestone: PH-06)

| Task ID | GitHub Issue Title | Work to Perform | Definition of Done | Priority | Mode | Target Milestone |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `PH-065` | Collect launch analytics | Review visitors, signups and activation | Launch metrics report | `launch:p1` | Analytics | `PH-06 — Post-Launch Stabilization` |
| `PH-066` | Analyze onboarding conversion | Find drop-off points | Funnel analysis completed | `launch:p1` | Analytics | `PH-06 — Post-Launch Stabilization` |
| `PH-067` | Analyze beta feedback | Categorize user feedback | Prioritized feedback backlog | `launch:p1` | Operations | `PH-06 — Post-Launch Stabilization` |
| `PH-068` | Resolve critical post-launch defects | Fix failures and regressions | Critical issues closed | `launch:p0` | Engineering | `PH-06 — Post-Launch Stabilization` |
| `PH-069` | Publish launch retrospective | Document outcomes and lessons | Retrospective published | `launch:p1` | Leadership | `PH-06 — Post-Launch Stabilization` |
| `PH-070` | Prepare next product iteration | Prioritize the next development cycle | Roadmap updated | `launch:p1` | Product | `PH-06 — Post-Launch Stabilization` |

---

## Strict Policy: Product Hunt Activities That Must Remain Manual

In accordance with official Product Hunt community guidelines, the following tasks must NEVER be automated via scripts, bots, or CI runners:
1. **Maker Identity & Account Creation**: Product Hunt requires personal accounts for makers.
2. **Product Submission & Draft Scheduling**: Human maker must submit and review fields.
3. **Maker Comment & Community Replies**: Authentic discussions and responses to questions.
4. **Upvotes & Voting Solicitation**: Absolutely no automated voting, syndicates, or artificial engagement manipulation.
