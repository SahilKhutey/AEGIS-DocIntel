# AEGIS-DocIntel — Product Hunt Launch Programme (PH-LAUNCH-01)

Welcome to the dedicated Product Hunt launch programme repository for **AEGIS-DocIntel**.

## Core Objective
Transform AEGIS-DocIntel from an internal engineering repository into a securely distributed, verifiable, and publicly recognized document intelligence product.

## Five Continuous Release Questions
The repository and automated GitHub Actions workflows answer these five questions at all times:
1. **Is the product ready to launch?** Verified via `backend-ci.yml`, `regression-tests.yml`, and `tests/product_development/`.
2. **Does the downloadable evaluation build actually work?** Verified via `release-install-tests.yml`, `tests/release/test_package_readiness_prot_final_11.py`, and Windows installer/portable ZIP packages.
3. **Is the public website and onboarding workflow working?** Verified via `marketing-preview.yml`, `website-smoke-tests.yml`, and `tests/security/product_hunt/test_ph_01_positioning_and_copy.py`.
4. **Are the release artifacts secure and verified?** Verified via `codeql.yml`, `secret-scan.yml`, `client-exposure-audit.yml`, `sbom.yml`, and `release-integrity.yml`.
5. **Is the team prepared to support users during and after launch?** Documented via `campaign/LAUNCH_DAY_RUNBOOK.md`, `listing/FAQ.md`, and `beta-feedback-triage.yml`.

## Directory Overview
- `strategy/`: Product positioning, target personas, and competitive analysis.
- `listing/`: Product Hunt listing copy, tagline, description, maker comment, and FAQs.
- `assets/`: Verified visual assets (logo, gallery SVGs, screenshots, demo storyboard).
- `website/`: Landing page copy, conversion funnel, and SEO metadata.
- `beta/`: Beta feedback framework, tester cohort tracking, and triage procedures.
- `campaign/`: 4-week launch timeline, launch-day runbook, and community guidelines.
- `analytics/`: Tracking plan, conversion funnels, and KPI metrics.
- `operations/`: The 70-task launch register (`LAUNCH_TASK_REGISTER.md`) and GitHub Project board schema (`GITHUB_PROJECT_STRUCTURE.md`).
- `release/`: Release checklist, limitations, and formal signoff charters.
- `reports/`: Audit summaries, test verification logs, and weekly status updates.
