"""
AEGIS-DocIntel Evaluation Gateway — Entitlement & Access Verification
Validates incoming evaluation tokens, cryptographic integrity, revocation, and feature entitlements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .license import (
    verify_license,
    parse_license_token,
    load_public_key,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseSignatureError,
    LicenseRevokedError,
)
from .revocation import registry as revocation_registry
from .quotas import quota_manager, QuotaExceededError

bearer_scheme = HTTPBearer(auto_error=False)

class EntitlementContext:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.license_id: str = payload["license_id"]
        self.user_id: str = payload.get("user_id", "evaluator")
        self.tier: str = payload.get("tier", "evaluation")
        self.features: List[str] = payload.get("features", [])
        self.quotas: Dict[str, int] = payload.get("quotas", {})

    def has_feature(self, feature_name: str) -> bool:
        return feature_name in self.features

    def require_feature(self, feature_name: str) -> None:
        if not self.has_feature(feature_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FEATURE_NOT_ENTITLED",
                    "feature": feature_name,
                    "message": f"Feature '{feature_name}' is not enabled in your evaluation tier. Contact sales@aegis-docintel.io to unlock full enterprise capabilities."
                }
            )


def extract_token_from_request(request: Request) -> Optional[str]:
    """Extracts evaluation license token from headers."""
    # Check custom X-Evaluation-License header first
    header_val = request.headers.get("X-Evaluation-License")
    if header_val:
        return header_val.strip()

    # Check standard Authorization Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # Check query param as fallback for SSE/streaming
    param = request.query_params.get("evaluation_token")
    if param:
        return param.strip()

    return None


def get_current_entitlement(request: Request) -> EntitlementContext:
    """
    FastAPI dependency that parses, verifies, and extracts license entitlement context.
    Raises clean HTTP 401 or 403 exceptions on failure.
    """
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "MISSING_EVALUATION_TOKEN",
                "message": "Evaluation license token required in 'X-Evaluation-License' or 'Authorization: Bearer <token>' header."
            }
        )

    try:
        license_doc = parse_license_token(token)
        payload = verify_license(
            license_doc=license_doc,
            public_key=load_public_key(),
            revocation_set=revocation_registry.get_revoked_set()
        )
    except LicenseExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "LICENSE_EXPIRED",
                "message": str(e)
            }
        )
    except LicenseRevokedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "LICENSE_REVOKED",
                "message": str(e)
            }
        )
    except LicenseSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_SIGNATURE",
                "message": "Cryptographic license verification failed. Token is tampered or forged."
            }
        )
    except LicenseVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_LICENSE",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTHENTICATION_FAILED",
                "message": "Failed to authenticate evaluation license."
            }
        )

    ctx = EntitlementContext(payload)

    # Check rate limit
    try:
        quota_manager.check_rate_limit(ctx.license_id)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": str(e)
            }
        )

    return ctx
