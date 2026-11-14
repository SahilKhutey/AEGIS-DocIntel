"""
src/services/evaluation/entitlement_service.py
==============================================
Central Server-Side Policy Evaluation and Authorization Decision Service.
Implements the four-factor authoritative formula:
ALLOW = Identity & License & Device & Entitlement & Resource & Quota
Complies with PROT-04 WP-04.05 specification.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.repositories.evaluation.entitlement_event_repository import (
    EntitlementEventRepository,
)
from src.repositories.evaluation.entitlement_policy_repository import (
    EntitlementPolicyRepository,
)
from src.repositories.evaluation.entitlement_repository import EntitlementRepository
from src.schemas.evaluation.authorization import (
    AuditReasonCode,
    AuthorizationDecision,
    DISALLOWED_EVALUATION_ROLES,
    PrincipalContext,
    SafeEntitlementResponse,
    SafeLicenseSummary,
    SafePrincipalSummary,
)
from src.schemas.evaluation.entitlement_catalogue import normalize_feature
from .entitlement_cache import EntitlementCache
from .entitlement_resolver import EntitlementResolver

logger = logging.getLogger("aegis.evaluation.entitlement_service")


class EntitlementService:
    """Central authoritative entitlement evaluation engine."""

    def __init__(
        self,
        *,
        policy_repo: Optional[EntitlementPolicyRepository] = None,
        entitlement_repo: Optional[EntitlementRepository] = None,
        event_repo: Optional[EntitlementEventRepository] = None,
        cache: Optional[EntitlementCache] = None,
    ) -> None:
        self.policy_repo = policy_repo or EntitlementPolicyRepository()
        self.entitlement_repo = entitlement_repo or EntitlementRepository()
        self.event_repo = event_repo or EntitlementEventRepository()
        self.cache = cache or EntitlementCache(ttl_seconds=60.0)
        self.resolver = EntitlementResolver(self.policy_repo, self.entitlement_repo)

    @property
    def current_revision(self) -> int:
        return self.policy_repo.revision + self.entitlement_repo.revision

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        permission: str,
        feature: str,
        resource: Optional[Any] = None,
        license_status: str = "ACTIVE",
        device_active: bool = True,
        is_revoked: bool = False,
    ) -> AuthorizationDecision:
        """
        Evaluates full authorization decision for principal, permission, feature, and resource.
        Guarantees fail-closed evaluation on any anomaly or exception.
        """
        norm_feature = normalize_feature(feature)

        try:
            # 1. Identity & RBAC Anti-Escalation Check (RBAC-001, RBAC-002, RBAC-003)
            if principal.is_evaluator:
                illegal_roles = set(principal.roles).intersection(DISALLOWED_EVALUATION_ROLES)
                if illegal_roles:
                    return self._record_and_return(
                        principal=principal,
                        feature=norm_feature,
                        permission=permission,
                        allowed=False,
                        reason_code=AuditReasonCode.ADMIN_ROLE_PROHIBITED.value,
                        details={"illegal_roles": list(illegal_roles)},
                    )

            # 2. License Status Check (ENT-003, ENT-004, ENT-005)
            if is_revoked:
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.LICENSE_REVOKED.value,
                )

            status_upper = (license_status or "ACTIVE").upper()
            if status_upper == "EXPIRED":
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.LICENSE_EXPIRED.value,
                )
            elif status_upper == "SUSPENDED":
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.LICENSE_SUSPENDED.value,
                )
            elif status_upper == "REVOKED":
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.LICENSE_REVOKED.value,
                )
            elif status_upper != "ACTIVE":
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.PERMISSION_DENIED.value,
                    details={"status": status_upper},
                )

            # 3. Device Binding Check (ENT-006)
            if not device_active:
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=AuditReasonCode.DEVICE_INACTIVE.value,
                )

            # 4. Entitlement & Permission Resolution (ENT-001, ENT-002, ENT-007 - ENT-015)
            license_id = principal.license_id or "default-evaluation-license"
            cached = self.cache.get(
                license_id=license_id,
                feature=norm_feature,
                permission=permission,
                current_revision=self.current_revision,
            )
            if cached is not None:
                allowed, reason_code = cached
            else:
                allowed, reason_code = self.resolver.evaluate_permission(
                    license_id=license_id,
                    feature=norm_feature,
                    permission=permission,
                )
                self.cache.set(
                    license_id=license_id,
                    feature=norm_feature,
                    permission=permission,
                    allowed=allowed,
                    reason_code=reason_code,
                    revision=self.current_revision,
                )

            if not allowed:
                return self._record_and_return(
                    principal=principal,
                    feature=norm_feature,
                    permission=permission,
                    allowed=False,
                    reason_code=reason_code,
                )

            # 5. Resource Ownership & Scope (TENANT-ENT-001 - TENANT-ENT-010)
            if resource is not None:
                res_tenant_id = getattr(resource, "tenant_id", None)
                if isinstance(resource, dict):
                    res_tenant_id = resource.get("tenant_id")

                if res_tenant_id and str(res_tenant_id) != str(principal.tenant_id):
                    return self._record_and_return(
                        principal=principal,
                        feature=norm_feature,
                        permission=permission,
                        allowed=False,
                        reason_code=AuditReasonCode.CROSS_TENANT_ACCESS_DENIED.value,
                        resource_id=getattr(resource, "id", str(resource)),
                    )

            # 6. All Checks Passed -> ALLOW
            return self._record_and_return(
                principal=principal,
                feature=norm_feature,
                permission=permission,
                allowed=True,
                reason_code=AuditReasonCode.ALLOWED.value,
            )

        except Exception as exc:
            # 7. Fail-Closed on Service Failure (ENT-018)
            logger.error(f"EntitlementService error: {exc}", exc_info=True)
            return self._record_and_return(
                principal=principal,
                feature=norm_feature,
                permission=permission,
                allowed=False,
                reason_code=AuditReasonCode.SERVICE_UNAVAILABLE.value,
                details={"error": str(exc)},
            )

    def get_safe_entitlements_summary(
        self,
        *,
        principal: PrincipalContext,
        license_status: str = "ACTIVE",
    ) -> SafeEntitlementResponse:
        """Constructs safe client-facing summary response (WP-04.05.07)."""
        license_id = principal.license_id or "default-evaluation-license"
        features_map, limits_map, policy_version_key = self.resolver.resolve_effective_entitlements(
            license_id=license_id
        )

        return SafeEntitlementResponse(
            principal=SafePrincipalSummary(
                id=principal.evaluator_id,
                role=principal.primary_role,
            ),
            license=SafeLicenseSummary(
                status=license_status.lower(),
                policy_version=policy_version_key,
            ),
            entitlements=features_map,
            limits=limits_map,
            version=self.current_revision,
        )

    def invalidate_cache(self, license_id: Optional[str] = None) -> None:
        self.cache.invalidate(license_id)

    def _record_and_return(
        self,
        *,
        principal: PrincipalContext,
        feature: str,
        permission: str,
        allowed: bool,
        reason_code: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuthorizationDecision:
        decision_str = "ALLOW" if allowed else "DENY"
        self.event_repo.record_event(
            event_type="ENTITLEMENT_" + ("GRANTED" if allowed else "DENIED"),
            principal_id=principal.evaluator_id,
            tenant_id=principal.tenant_id,
            license_id=principal.license_id,
            feature=feature,
            permission=permission,
            decision=decision_str,
            reason_code=reason_code,
            resource_id=resource_id,
            details=details,
        )
        return AuthorizationDecision(
            allowed=allowed,
            reason_code=reason_code,
            feature=feature,
            permission=permission,
            resource_id=resource_id,
            details=details,
        )


# Global singleton instance for easy import and dependency injection
default_entitlement_service = EntitlementService()
