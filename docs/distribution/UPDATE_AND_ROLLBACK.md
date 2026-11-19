# AEGIS-DocIntel Update and Rollback Engineering Specification

**Specification Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-11 (Section 8)  
**Classification:** Canonical Engineering Specification  
**Status:** APPROVED & ADOPTED  

---

## 1. Executive Summary

This document specifies the update lifecycle, channel policy, cryptographic verification, and automated rollback procedures for the AEGIS-DocIntel downloadable evaluation distribution. 

### Security Mandate
Automatic updaters that download and execute arbitrary binaries from untrusted or unverified URLs are strictly prohibited. Every update must be:
1. Cryptographically signed using the release authority's offline Ed25519 signing key.
2. Verified against an authoritative SHA-256 manifest before staging.
3. Preceded by an atomic snapshot of local client configuration.
4. Protected by an automated health probe that triggers immediate rollback if the new version fails startup.

---

## 2. Update Lifecycle State Machine

```
               +-----------------------------------+
               |         Installed Version         |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |   Check Signed Update Metadata    |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |  Verify Channel & Version Policy  |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |       Download Update Bundle      |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |    Verify Signature & SHA-256     |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               | Validate Platform & Compatibility |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |      Install Staged Update        |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |     Run Startup Health Check      |
               +-----------------+-----------------+
                                / \
                       Success /   \ Failure
                              /     \
                             v       v
           +------------------+     +------------------+
           | Record Installed |     | Execute Rollback |
           |     Version      |     | To Prior Snapshot|
           +------------------+     +------------------+
```

---

## 3. Update Policy & Channel Architecture

### 3.1 Distribution Channels
- **Stable Channel (`stable`):** Production releases thoroughly vetted through internal alpha, technical beta, and public beta stages (e.g. `1.0.0`, `1.1.0`).
- **Beta Channel (`beta`):** Evaluation releases provided to invited technical testers and design partners (e.g. `1.0.0-beta.1`, `1.0.0-beta.2`).

### 3.2 Invariants & Rules
1. **No Automatic Downgrades:** The client will never install an update whose semantic version is lower than the current version unless explicitly instructed via administrative force-downgrade flags.
2. **Atomic Configuration Backup:** Before applying files, the updater preserves `config/client.json` and local cache into `backups/pre-update-<timestamp>/`.
3. **Data Immutability:** User documents in the workspace directory are never modified or overwritten during an application update.
4. **Offline Capability:** If update servers are unreachable, the application continues normal operation on the currently installed version.

---

## 4. Rollback Protocol

If the newly staged update fails its local health check probe (`GET http://127.0.0.1:3000/health`) within 30 seconds of launch:
1. **Immediate Process Termination:** The launcher shuts down all child processes associated with the failed update.
2. **Snapshot Restoration:** Files from `backups/pre-update-<timestamp>/` are restored over the application directory.
3. **Audit Event Recording:** A local failure diagnostic record (`UPDATE_ROLLBACK_OCCURRED`) is written to `logs/update-events.log`.
4. **User Notification:** A clear UI prompt notifies the evaluator that the update failed and the prior operational version has been safely restored.

---

## 5. Uninstallation Lifecycle

The uninstallation process (managed by the Windows Inno Setup uninstaller or portable removal script):
1. **Process Teardown:** Confirms all background AEGIS launcher and proxy processes are stopped.
2. **Binary Purge:** Removes application binaries, frontend assets, launcher scripts, and desktop shortcuts.
3. **User Data Option:** Prompts the user whether to preserve or purge local documents, session caches, and operational logs.
4. **Registry & Environment Cleanliness:** Removes registered Windows uninstaller entries from `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\AEGIS-DocIntel`.
