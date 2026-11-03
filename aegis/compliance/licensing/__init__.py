"""
aegis.compliance.licensing
==========================
Dependency license scanner and license architecture reconciler.
"""
from .scanner import DependencyLicenseScanner, LicenseClassification, LicenseInfo

__all__ = ["DependencyLicenseScanner", "LicenseClassification", "LicenseInfo"]
