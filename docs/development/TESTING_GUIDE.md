# Testing Guide

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## Running Test Suites
```powershell
# Full central audit (WP-01 to WP-FINAL)
python -m aegis.audit run

# Individual unit and integration suites
pytest tests/unit/ -v
pytest tests/security/ tests/reliability/ -v
```
