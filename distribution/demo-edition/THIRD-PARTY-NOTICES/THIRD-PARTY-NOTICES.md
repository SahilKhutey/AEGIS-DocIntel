# AEGIS-DocIntel Demo Edition — Third-Party Notices & Licenses

**Product:** AEGIS-DocIntel Protected Demo Edition  
**Version:** v1.1.0  
**Audit Specification:** PROT-02 Third-Party Dependency & License Audit  

This document and associated directories provide attribution and licensing information for third-party software, fonts, icons, data, and libraries incorporated into or distributed with the AEGIS-DocIntel Demo Edition.

The complete machine-readable software bills of materials (SBOMs) and license register are located in:
- `manifest/npm-sbom.json` (CycloneDX 1.5 format for frontend dependencies)
- `manifest/python-sbom.json` (CycloneDX format for backend environment)
- `manifest/dependency-license-register.csv` (complete audit register)

Individual license texts are provided in the `licenses/` directory.

---

## 1. Primary Runtime Components

### A. Next.js & React Ecosystem
- **Packages:** `next` (v16.4.3), `react` (v19.3.0), `react-dom` (v19.3.0)
- **License:** MIT License (`licenses/MIT.txt`)
- **Copyright:**
  - Next.js: Copyright (c) 2026 Vercel, Inc.
  - React: Copyright (c) Meta Platforms, Inc. and affiliates.
- **Notice:** Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.

### B. Lucide Icons
- **Package:** `lucide-react` (v1.70.0)
- **License:** ISC License (`licenses/ISC.txt`)
- **Copyright:** Copyright (c) 2022 Lucide Contributors, Copyright (c) 2013-2022 Cole Bemis
- **Notice:** Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.

### C. Zod
- **Package:** `zod` (v4.6.7)
- **License:** MIT License (`licenses/MIT.txt`)
- **Copyright:** Copyright (c) 2020 Colin McDonnell

### D. Nginx Reverse Proxy Container
- **Package:** `nginx:alpine`
- **License:** 2-Clause BSD License (`licenses/BSD-2-Clause.txt`)
- **Copyright:** Copyright (c) 2002-2026 Igor Sysoev, Copyright (c) 2011-2026 Nginx, Inc.

### E. Cryptography (Asymmetric Verification)
- **Package:** `pyca/cryptography`
- **License:** Apache License 2.0 (`licenses/Apache-2.0.txt`) / BSD 3-Clause (`licenses/BSD-3-Clause.txt`)
- **Copyright:** Copyright (c) Individual contributors.

---

## 2. Open-Core Component: aegis-docprep
- **Package:** `aegis-docprep` (v0.1.0)
- **License:** Apache License 2.0 (`licenses/Apache-2.0.txt`)
- **Copyright:** Copyright 2026 AEGIS Systems Inc. / Sahil Khutey
- **Notice:** Licensed under the Apache License, Version 2.0. See `licenses/Apache-2.0.txt`.

---

## 3. Special License Considerations & Findings

### A. Finding DEP-001: Sharp & libvips (LGPL-3.0-or-later)
- **Packages:** `@img/sharp-libvips-*`, `@img/sharp-*`
- **License:** LGPL-3.0-or-later (`licenses/LGPL-3.0-or-later.txt`) and Apache-2.0
- **Notice:** Next.js utilizes dynamic bindings for optional image processing. In the production container, shared object bindings are retained dynamically. In accordance with Section 4(d) of LGPL-3.0, users are permitted to replace or relink compatible versions of libvips.

### B. Finding DEP-002: MPL-2.0 Components
- **Packages:** `axe-core`, `@axe-core/playwright`, `lightningcss`
- **License:** Mozilla Public License 2.0 (`licenses/MPL-2.0.txt`)
- **Notice:** These packages are utilized exclusively in development and automated testing pipelines (`devDependencies`). They are omitted from the production standalone client runtime bundle.

### C. Finding DEP-003: Caniuse-Lite (CC-BY-4.0)
- **Package:** `caniuse-lite`
- **License:** Creative Commons Attribution 4.0 International (`licenses/CC-BY-4.0.txt`)
- **Copyright:** Copyright (c) Alexis Deveria
- **Notice:** Data provided under CC-BY-4.0. Upstream source available at `https://github.com/browserslist/caniuse-lite`.

### D. Finding DEP-004: Blue Oak Model License
- **Packages:** `lru-cache`, `minimatch` (transitive devDependencies)
- **License:** Blue Oak Model License 1.0.0 (`licenses/BlueOak-1.0.0.txt`)
- **Notice:** Preserved in dev dependency tree in accordance with Blue Oak 1.0.0 terms.

### E. Finding DEP-005: Backend Python Dependency Exclusion
- **Packages:** `pymupdf` (AGPL-3.0), `poppler-utils` (GPL), `fastapi`, `openai`, `anthropic`, `torch`, `scikit-learn`
- **Status:** **EXCLUDED FROM DOWNLOADABLE DEMO PACKAGE**.
- **Notice:** All backend processing and AI orchestration execute remotely on AEGIS-controlled private infrastructure behind the Evaluation Gateway. This architectural boundary prevents AGPL/GPL copyleft contamination and eliminates local dependency vulnerabilities.
