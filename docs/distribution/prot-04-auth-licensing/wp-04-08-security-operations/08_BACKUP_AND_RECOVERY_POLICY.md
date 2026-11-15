# PROT-04.08 — Dossier 08: Backup, Recovery & Fail-Closed State Reconciliation

## 1. Disaster Recovery & State Integrity
Disaster recovery for the Protected Demo Edition must preserve security guarantees across restore events. In particular, restoring a database snapshot must never undo administrative security decisions made after that snapshot was captured.

---

## 2. Checksum Verification Protocol
All database backups and snapshot exports generate a cryptographic SHA-256 digest computed over the canonical representation of the exported dataset:

$$\text{Checksum} = \text{SHA256}\big(\text{Canonical}(\text{BackupPayload})\big)$$

Prior to restoring any backup, `backup_verification_service.verify_backup_integrity(backup_id)` verifies the candidate payload against the stored checksum. If a single byte has been modified or corrupted, restore is refused fail-closed.

---

## 3. The Non-Resurrection Rule
A critical vulnerability in traditional backup restore systems is **state resurrection**:
> *Scenario*: A malicious evaluator's license is revoked at 14:00 UTC. At 15:00 UTC, an unrelated database crash occurs. The operator restores the 13:00 UTC snapshot. If not reconciled, the malicious license is resurrected as valid.

### Reconciled Restore Algorithm
To eliminate this vulnerability, `restore_and_reconcile` enforces authoritative reconciliation:

```python
def restore_and_reconcile(
    backup_id: str,
    authoritative_revocations: Optional[Set[str]] = None
) -> Tuple[bool, Dict[str, Any]]:
    # 1. Verify backup checksum integrity
    # 2. Extract snapshot state
    # 3. Query authoritative external revocation registry
    # 4. Overwrite snapshot license/session status with authoritative revocations
    # 5. Guarantee revoked entities remain strictly revoked
```

### Verification Evidence:
- Restoring a stale snapshot containing active records for licenses `lic-stale-001` and `lic-stale-002` when they exist in `authoritative_revocations` guarantees that after restore, both licenses remain revoked.
- Empirical test `test_ir_006_restore_stale_snapshot_non_resurrection_rule` passes 100% green.
