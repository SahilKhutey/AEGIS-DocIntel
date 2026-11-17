"""
src/schemas/evaluation/entitlement_catalogue.py
===============================================
Canonical Feature and Permission Catalogue for AEGIS-DocIntel Evaluation Edition.
Defines immutable feature identifiers, action-level permissions, and structural mappings.
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Set

# 1. Canonical Feature Catalogue
FEATURE_DASHBOARD_VIEW = "dashboard.view"
FEATURE_DOCUMENT_UPLOAD = "document.upload"
FEATURE_DOCUMENT_PREVIEW = "document.preview"
FEATURE_DOCUMENT_METADATA = "document.metadata"
FEATURE_DOCUMENT_PARSE = "document.parse"
FEATURE_DOCUMENT_QUERY = "document.query"
FEATURE_DOCUMENT_COMPARE = "document.compare"
FEATURE_DOCUMENT_EXPORT = "document.export"
FEATURE_WORKSPACE_MANAGE = "workspace.manage"
FEATURE_USAGE_VIEW = "usage.view"
FEATURE_LICENSE_VIEW = "license.view"
FEATURE_DEVICE_MANAGE = "device.manage"

# Administrative Features (strictly forbidden for evaluators)
FEATURE_ADMIN_MANAGE_USERS = "admin.manage_users"
FEATURE_ADMIN_ISSUE_LICENSE = "admin.issue_license"
FEATURE_ADMIN_REVOKE_LICENSE = "admin.revoke_license"
FEATURE_ENGINE_ADMIN = "engine.admin"
FEATURE_INTERNAL_DEBUG = "internal.debug"

EVALUATION_FEATURES: FrozenSet[str] = frozenset({
    FEATURE_DASHBOARD_VIEW,
    FEATURE_DOCUMENT_UPLOAD,
    FEATURE_DOCUMENT_PREVIEW,
    FEATURE_DOCUMENT_METADATA,
    FEATURE_DOCUMENT_PARSE,
    FEATURE_DOCUMENT_QUERY,
    FEATURE_DOCUMENT_COMPARE,
    FEATURE_DOCUMENT_EXPORT,
    FEATURE_WORKSPACE_MANAGE,
    FEATURE_USAGE_VIEW,
    FEATURE_LICENSE_VIEW,
    FEATURE_DEVICE_MANAGE,
})

ADMIN_FEATURES: FrozenSet[str] = frozenset({
    FEATURE_ADMIN_MANAGE_USERS,
    FEATURE_ADMIN_ISSUE_LICENSE,
    FEATURE_ADMIN_REVOKE_LICENSE,
    FEATURE_ENGINE_ADMIN,
    FEATURE_INTERNAL_DEBUG,
})

ALL_CANONICAL_FEATURES: FrozenSet[str] = EVALUATION_FEATURES | ADMIN_FEATURES

# 2. Canonical Action-Level Permissions (<resource>.<action>)
PERM_DOCUMENT_READ = "document.read"
PERM_DOCUMENT_UPLOAD = "document.upload"
PERM_DOCUMENT_PARSE = "document.parse"
PERM_DOCUMENT_QUERY = "document.query"
PERM_DOCUMENT_COMPARE = "document.compare"
PERM_DOCUMENT_EXPORT = "document.export"
PERM_DOCUMENT_DELETE = "document.delete"
PERM_WORKSPACE_READ = "workspace.read"
PERM_WORKSPACE_UPDATE = "workspace.update"
PERM_USAGE_READ = "usage.read"
PERM_LICENSE_READ = "license.read"
PERM_DEVICE_DEACTIVATE = "device.deactivate"

# Administrative Permissions (strictly forbidden in evaluator policies)
PERM_ADMIN_EVALUATION_ISSUE = "admin.evaluation.issue"
PERM_ADMIN_EVALUATION_SUSPEND = "admin.evaluation.suspend"
PERM_ADMIN_EVALUATION_REVOKE = "admin.evaluation.revoke"
PERM_ADMIN_EVALUATION_INSPECT = "admin.evaluation.inspect"
PERM_ADMIN_USERS_MANAGE = "admin.users.manage"
PERM_ADMIN_ENGINE_MANAGE = "admin.engine.manage"

EVALUATION_PERMISSIONS: FrozenSet[str] = frozenset({
    PERM_DOCUMENT_READ,
    PERM_DOCUMENT_UPLOAD,
    PERM_DOCUMENT_PARSE,
    PERM_DOCUMENT_QUERY,
    PERM_DOCUMENT_COMPARE,
    PERM_DOCUMENT_EXPORT,
    PERM_DOCUMENT_DELETE,
    PERM_WORKSPACE_READ,
    PERM_WORKSPACE_UPDATE,
    PERM_USAGE_READ,
    PERM_LICENSE_READ,
    PERM_DEVICE_DEACTIVATE,
})

ADMIN_PERMISSIONS: FrozenSet[str] = frozenset({
    PERM_ADMIN_EVALUATION_ISSUE,
    PERM_ADMIN_EVALUATION_SUSPEND,
    PERM_ADMIN_EVALUATION_REVOKE,
    PERM_ADMIN_EVALUATION_INSPECT,
    PERM_ADMIN_USERS_MANAGE,
    PERM_ADMIN_ENGINE_MANAGE,
})

ALL_CANONICAL_PERMISSIONS: FrozenSet[str] = EVALUATION_PERMISSIONS | ADMIN_PERMISSIONS

# 3. Feature-to-Required-Permissions Mapping
FEATURE_REQUIRED_PERMISSIONS: Dict[str, Set[str]] = {
    FEATURE_DASHBOARD_VIEW: {PERM_USAGE_READ, PERM_LICENSE_READ},
    FEATURE_DOCUMENT_UPLOAD: {PERM_DOCUMENT_UPLOAD},
    FEATURE_DOCUMENT_PREVIEW: {PERM_DOCUMENT_READ},
    FEATURE_DOCUMENT_METADATA: {PERM_DOCUMENT_READ},
    FEATURE_DOCUMENT_PARSE: {PERM_DOCUMENT_PARSE, PERM_DOCUMENT_READ},
    FEATURE_DOCUMENT_QUERY: {PERM_DOCUMENT_QUERY, PERM_DOCUMENT_READ},
    FEATURE_DOCUMENT_COMPARE: {PERM_DOCUMENT_COMPARE, PERM_DOCUMENT_READ},
    FEATURE_DOCUMENT_EXPORT: {PERM_DOCUMENT_EXPORT, PERM_DOCUMENT_READ},
    FEATURE_WORKSPACE_MANAGE: {PERM_WORKSPACE_READ, PERM_WORKSPACE_UPDATE},
    FEATURE_USAGE_VIEW: {PERM_USAGE_READ},
    FEATURE_LICENSE_VIEW: {PERM_LICENSE_READ},
    FEATURE_DEVICE_MANAGE: {PERM_DEVICE_DEACTIVATE},
    FEATURE_ADMIN_MANAGE_USERS: {PERM_ADMIN_USERS_MANAGE},
    FEATURE_ADMIN_ISSUE_LICENSE: {PERM_ADMIN_EVALUATION_ISSUE},
    FEATURE_ADMIN_REVOKE_LICENSE: {PERM_ADMIN_EVALUATION_REVOKE},
    FEATURE_ENGINE_ADMIN: {PERM_ADMIN_ENGINE_MANAGE},
    FEATURE_INTERNAL_DEBUG: {PERM_ADMIN_ENGINE_MANAGE},
}

# 4. Backward-compatibility alias map from older names
LEGACY_FEATURE_MAP: Dict[str, str] = {
    "document_upload": FEATURE_DOCUMENT_UPLOAD,
    "document_extraction": FEATURE_DOCUMENT_PREVIEW,
    "ask_aegis": FEATURE_DOCUMENT_QUERY,
    "citation_inspection": FEATURE_DOCUMENT_PREVIEW,
    "document_comparison": FEATURE_DOCUMENT_COMPARE,
    "synthetic_ground_truth": FEATURE_DOCUMENT_PREVIEW,
    "documents.read": FEATURE_DOCUMENT_PREVIEW,
    "documents.upload": FEATURE_DOCUMENT_UPLOAD,
    "intelligence.query": FEATURE_DOCUMENT_QUERY,
    "documents.compare": FEATURE_DOCUMENT_COMPARE,
    "evidence.inspect": FEATURE_DOCUMENT_PREVIEW,
}


LEGACY_PERMISSION_MAP: Dict[str, str] = {
    "documents.upload": PERM_DOCUMENT_UPLOAD,
    "documents.read": PERM_DOCUMENT_READ,
    "documents.compare": PERM_DOCUMENT_COMPARE,
    "intelligence.query": PERM_DOCUMENT_QUERY,
    "evidence.inspect": PERM_DOCUMENT_READ,
    "documents.export": PERM_DOCUMENT_EXPORT,
    "documents.delete": PERM_DOCUMENT_DELETE,
}


def normalize_feature(feature_name: str) -> str:
    """Returns canonical feature ID or legacy mapped feature ID."""
    return LEGACY_FEATURE_MAP.get(feature_name, feature_name)


def normalize_permission(permission_name: str) -> str:
    """Returns canonical action permission."""
    return LEGACY_PERMISSION_MAP.get(permission_name, permission_name)


def is_known_feature(feature_name: str) -> bool:
    """Returns True if the feature exists in the canonical feature catalogue."""
    norm = normalize_feature(feature_name)
    return norm in ALL_CANONICAL_FEATURES


def is_known_permission(permission_name: str) -> bool:
    """Returns True if the permission exists in the canonical permission catalogue."""
    norm = normalize_permission(permission_name)
    return norm in ALL_CANONICAL_PERMISSIONS


def is_admin_permission(permission_name: str) -> bool:
    """Returns True if permission is administrative."""
    return permission_name in ADMIN_PERMISSIONS or permission_name.startswith("admin.")
