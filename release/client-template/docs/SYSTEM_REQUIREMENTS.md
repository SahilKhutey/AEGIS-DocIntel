# AEGIS-DocIntel Evaluation Client — System Requirements

**Version:** 1.0.0-beta.1  

---

## 1. Operating System
- **Supported Platforms:** Windows 10 (64-bit, Version 2004 / Build 19041 or higher) or Windows 11 (64-bit).
- **Architecture:** x86_64 / AMD64.
- **Privilege Level:** Standard user account (Administrative elevation not required for standard installation).

---

## 2. Hardware Specifications
- **CPU:** Dual-core 2.0 GHz or faster x86_64 processor.
- **Memory (RAM):**
  - Minimum: 4 GB.
  - Recommended: 8 GB.
- **Disk Space:**
  - 500 MB free storage for application binaries and cached frontend assets.
  - Additional 1 GB recommended for document caching during multi-document analysis.
- **Display Resolution:** Minimum 1280 x 720 (1920 x 1080 recommended).

---

## 3. Network Requirements
- **Outbound Connectivity:** TCP Port 443 (HTTPS) to the designated AEGIS Evaluation Gateway.
- **Loopback Access:** TCP Port binding on `127.0.0.1` for local launcher and UI communication.
- **Firewall Configuration:** No inbound ports need to be opened on your network or firewall.
