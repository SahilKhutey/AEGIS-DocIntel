# AEGIS-DocIntel Demo Edition — Third-Party Notices & Licenses

**Product:** AEGIS-DocIntel Protected Demo Edition  
**Version:** v1.1.0  
**Audit Standard:** PROT-02 Third-Party Dependency & License Audit  

The AEGIS-DocIntel Demo Edition incorporates or interacts with third-party software components licensed under permissive open-source and standard public terms. This distribution includes full license texts in `THIRD-PARTY-NOTICES/licenses/` and complete machine-readable CycloneDX SBOMs and registers in `THIRD-PARTY-NOTICES/manifest/`.

---

### 1. aegis-docprep
- **Project:** AEGIS Document Preparation Suite
- **License:** Apache License 2.0 (`THIRD-PARTY-NOTICES/licenses/Apache-2.0.txt`)
- **Copyright:** Copyright 2026 AEGIS Systems Inc. / Sahil Khutey
- **Notice:** Licensed under the Apache License, Version 2.0. Upstream repository: `https://github.com/SahilKhutey/AEGIS-DocIntel`.

---

### 2. Next.js & React
- **Project:** Next.js (Vercel, Inc.) & React (Meta Platforms, Inc.)
- **License:** MIT License (`THIRD-PARTY-NOTICES/licenses/MIT.txt`)
- **Copyright:** Copyright (c) 2026 Vercel, Inc. / Meta Platforms, Inc. and affiliates.
- **Notice:** Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.

---

### 3. Lucide Icons
- **Project:** Lucide Icons (Lucide Project)
- **License:** ISC License (`THIRD-PARTY-NOTICES/licenses/ISC.txt`)
- **Copyright:** Copyright (c) 2022 Lucide Contributors, Copyright (c) 2013-2022 Cole Bemis

---

### 4. Zod & Tailwind CSS
- **Projects:** Zod (Colin McDonnell) & Tailwind CSS (Tailwind Labs, Inc.)
- **License:** MIT License (`THIRD-PARTY-NOTICES/licenses/MIT.txt`)
- **Copyright:** Copyright (c) 2020 Colin McDonnell / Tailwind Labs, Inc.

---

### 5. Nginx (Open Source)
- **Project:** Nginx Reverse Proxy
- **License:** 2-Clause BSD License (`THIRD-PARTY-NOTICES/licenses/BSD-2-Clause.txt`)
- **Copyright:** Copyright (c) 2002-2026 Igor Sysoev / Nginx, Inc.

---

### 6. Cryptography (pyca/cryptography)
- **Project:** Python Cryptographic Authority
- **License:** Apache License 2.0 (`THIRD-PARTY-NOTICES/licenses/Apache-2.0.txt`) / BSD 3-Clause (`THIRD-PARTY-NOTICES/licenses/BSD-3-Clause.txt`)
- **Copyright:** Copyright (c) Individual contributors.

---

### 7. Caniuse-Lite
- **Project:** Caniuse-Lite (Browserslist)
- **License:** Creative Commons Attribution 4.0 International (`THIRD-PARTY-NOTICES/licenses/CC-BY-4.0.txt`)
- **Copyright:** Copyright (c) Alexis Deveria

---

### 8. Backend & Cloud Service Separation
All proprietary document intelligence algorithms, Sheaf Laplacian models, submodular context optimizers, and heavy backend dependencies (PyMuPDF, Poppler, PyTorch, FastAPI, OpenAI, Anthropic) execute **remotely** on AEGIS cloud infrastructure behind the Evaluation Gateway. They are excluded from this downloadable package to protect proprietary IP and prevent AGPL/GPL copyleft contamination.
