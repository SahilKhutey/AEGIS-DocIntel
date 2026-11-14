"""
AEGIS-DocIntel Evaluation Gateway — Entitlement & Access Verification
Validates incoming evaluation tokens, cryptographic integrity, revocation, and feature entitlements.
Complies with PROT-04 WP-04.05 specifications.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer

from .license import (
    verify_license,
    parse_license_token,
    load_public_key,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseSignatureError,
    LicenseRevokedError,
    LicenseSuspendedError,
    LicenseProductMismatchError,
)
from .revocation import registry as revocation_registry
from .quotas import quota_manager, QuotaExceededError
from .audit import audit_service

bearer_scheme = HTTPBearer(auto_error=False)

CANONICAL_ENTITLEMENTS: Set[str] = {
    "documents.read",
    "documents.upload",
    "intelligence.query",
    "documents.compare",
    "evidence.inspect",
}

DISALLOWED_ENTITLEMENTS: Set[str] = {
    "users.manage",
    "platform.admin",
    "workspaces.create",
    "models.configure",
    "integrations.manage",
    "admin.api",
}

# Compatibility mapping between old feature names and canonical capabilities
FEATURE_MAP: Dict[str, str] = {
    "document_upload": "documents.upload",
    "document_extraction": "documents.read",
    "ask_aegis": "intelligence.query",
    "citation_inspection": "evidence.inspect",
    "document_comparison": "documents.compare",
    "synthetic_ground_truth": "documents.read",
}


class EntitlementContext:
    def __init__(self, payload: Dict[str, Any], session_info: Optional[Dict[str, Any]] = None):
        self.payload = payload
        self.session_info = session_info or {}
        self.license_id: str = payload.get("license_id", "unknown-license")
        self.user_id: str = payload.get("user_id") or payload.get("subject", "evaluator")
        self.tier: str = payload.get("tier", "evaluation")
        self.features: List[str] = payload.get("features", [])
        self.entitlements: List[str] = payload.get("entitlements", self.features)
        self.quotas: Dict[str, int] = payload.get("quotas", {})
        self.device_id: Optional[str] = self.session_info.get("device_id")

    def has_feature(self, feature_name: str) -> bool:
        canonical = FEATURE_MAP.get(feature_name, feature_name)
        if canonical in DISALLOWED_ENTITLEMENTS:
            return False

        # Authoritative policy & override resolution from EntitlementService
        try:
            if hasattr(self, "license_id") and self.license_id:
                from src.services.evaluation.entitlement_service import default_entitlement_service
                assignment = default_entitlement_service.entitlement_repo.get_assignment(self.license_id)
                overrides = default_entitlement_service.entitlement_repo.get_overrides(self.license_id)
                if assignment or overrides:
                    allowed, reason = default_entitlement_service.resolver.evaluate_permission(
                        license_id=self.license_id,
                        feature=feature_name,
                        permission=canonical,
                    )
                    return allowed
        except Exception:
            pass

        return (
            feature_name in self.features
            or canonical in self.entitlements
            or canonical in self.features
        )

    def require_feature(self, feature_name: str) -> None:
        if not self.has_feature(feature_name):
            audit_service.record_event(
                event_type="entitlement.denied",
                status="FORBIDDEN",
                actor_id=self.user_id,
                license_id=self.license_id,
                resource=feature_name,
                details={"feature": feature_name},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FEATURE_NOT_ENTITLED",
                    "feature": feature_name,
                    "message": f"Feature '{feature_name}' is not enabled in your evaluation tier. Contact sales@aegis-docintel.io to unlock full enterprise capabilities."
                }
            )


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extracts evaluation license token or session bearer token from request headers."""
    # 1. Custom evaluation header
    header_val = request.headers.get("X-Evaluation-License")
    if header_val:
        return header_val.strip()

    # 2. Standard Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # 3. Query param fallback
    param = request.query_params.get("evaluation_token")
    if param:
        return param.strip()

    return None


def get_current_entitlement(request: Request) -> EntitlementContext:
    """
    FastAPI dependency that parses, verifies, and extracts license entitlement context.
    Supports both signed evaluation tokens and short-lived session access tokens.
    Guarantees server-side source of truth (rejects ENT-004, ENT-005).
    """
    token = extract_token_from_request(request)
    if not token:
        audit_service.record_event(
            event_type="auth.missing_token",
            status="UNAUTHORIZED",
            actor_id="anonymous",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "MISSING_EVALUATION_TOKEN",
                "message": "Evaluation license token or session token required in 'X-Evaluation-License' or 'Authorization: Bearer <token>' header."
            }
        )

    # Lazily import to prevent cyclic imports
    from .activation import activation_service

    # Check if token is a session access token (aegis_eval_at_...)
    if token.startswith("aegis_eval_at_"):
        session_rec = activation_service.validate_session(token)
        if not session_rec:
            audit_service.record_event(
                event_type="session.invalid_or_expired",
                status="UNAUTHORIZED",
                actor_id="anonymous",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_SESSION",
                    "message": "Evaluation session token is invalid, expired, or logged out."
                }
            )

        # Immediate revocation check (SESSION-003, LIC-004)
        if revocation_registry.is_revoked(session_rec.license_id):
            audit_service.record_event(
                event_type="session.license_revoked",
                status="FORBIDDEN",
                actor_id=session_rec.user_id,
                license_id=session_rec.license_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "LICENSE_REVOKED",
                    "message": f"License {session_rec.license_id} has been revoked. All active sessions terminated."
                }
            )

        payload = {
            "license_id": session_rec.license_id,
            "user_id": session_rec.user_id,
            "tier": "evaluation",
            "features": [
                "documents.read",
                "documents.upload",
                "intelligence.query",
                "documents.compare",
                "evidence.inspect",
                "document_upload",
                "ask_aegis",
                "document_comparison",
            ],
            "entitlements": [
                "documents.read",
                "documents.upload",
                "intelligence.query",
                "documents.compare",
                "evidence.inspect",
            ],
            "quotas": {
                "max_documents": 5,
                "max_queries_per_day": 20,
                "max_comparisons_per_day": 5,
                "max_file_size_mb": 10,
                "max_storage_mb": 100,
            },
        }
        ctx = EntitlementContext(payload, session_info={"device_id": session_rec.device_id})

    else:
        # Cryptographic license token verification
        try:
            license_doc = parse_license_token(token)
            payload = verify_license(
                license_doc=license_doc,
                public_key=load_public_key(),
                revocation_set=revocation_registry.get_revoked_set(),
            )
        except LicenseExpiredError as e:
            audit_service.record_event(
                event_type="license.expired",
                status="FORBIDDEN",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "LICENSE_EXPIRED", "message": str(e)}
            )
        except LicenseRevokedError as e:
            audit_service.record_event(
                event_type="license.revoked",
                status="FORBIDDEN",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "LICENSE_REVOKED", "message": str(e)}
            )
        except LicenseSuspendedError as e:
            audit_service.record_event(
                event_type="license.suspended",
                status="FORBIDDEN",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "LICENSE_SUSPENDED", "message": str(e)}
            )
        except LicenseProductMismatchError as e:
            audit_service.record_event(
                event_type="license.product_mismatch",
                status="FORBIDDEN",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "PRODUCT_MISMATCH", "message": str(e)}
            )
        except LicenseSignatureError as e:
            audit_service.record_event(
                event_type="license.signature_invalid",
                status="UNAUTHORIZED",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "INVALID_SIGNATURE",
                    "message": "Cryptographic license verification failed. Token is tampered or forged."
                }
            )
        except LicenseVerificationError as e:
            audit_service.record_event(
                event_type="license.verification_error",
                status="BAD_REQUEST",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "INVALID_LICENSE", "message": str(e)}
            )
        except Exception as e:
            audit_service.record_event(
                event_type="auth.failed",
                status="UNAUTHORIZED",
                actor_id="evaluator",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "AUTHENTICATION_FAILED", "message": "Failed to authenticate evaluation license."}
            )

        ctx = EntitlementContext(payload)

    # Rate limiting check
    try:
        quota_manager.check_rate_limit(ctx.license_id)
    except QuotaExceededError as e:
        audit_service.record_event(
            event_type="quota.rate_limit_exceeded",
            status="RATE_LIMITED",
            actor_id=ctx.user_id,
            license_id=ctx.license_id,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "RATE_LIMIT_EXCEEDED", "message": str(e)}
        )

    return ctx
