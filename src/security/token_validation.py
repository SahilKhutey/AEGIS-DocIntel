"""
AEGIS-DocIntel Evaluation Token Validation (PROT-FINAL-02 / REM-01)
Enforces RS256 signature verification, mandatory issuer/audience claims,
approved role validation, and strict rejection of development bypass tokens.
"""

from __future__ import annotations

import os
from typing import Any, Dict, FrozenSet, Optional

from fastapi import HTTPException, status
import jwt

from src.core.security_context import STANDARD_ROLES, TenantContext
from src.api.auth import validate_token_roles, ALLOWED_ROLES


class EvaluationTokenValidator:
    def __init__(
        self,
        public_key: Optional[str] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
    ):
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience

    def get_public_key(self) -> str:
        pk = self._public_key or os.environ.get("AEGIS_JWT_PUBLIC_KEY")
        if not pk:
            pk_path = os.environ.get("AEGIS_JWT_PUBLIC_KEY_PATH")
            if pk_path and os.path.isfile(pk_path):
                with open(pk_path, "r", encoding="utf-8") as f:
                    pk = f.read()
        if not pk:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT validation not configured: public key missing",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return pk

    def validate_token(
        self,
        token: str,
        expected_issuer: Optional[str] = None,
        expected_audience: Optional[str] = None,
        strict_evaluation: bool = True,
    ) -> TenantContext:
        """
        Validates an evaluation RS256 token according to REM-01 specifications:
        1. Dev tokens strictly rejected in production.
        2. RS256 cryptographic verification.
        3. Mandatory exp, sub, iss, and aud in strict/evaluation mode.
        4. Strict role validation against approved catalogue.
        5. Tenant context derived authoritatively from token.
        """
        env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
        if token.startswith("dev-"):
            if env != "development":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Development tokens are strictly rejected in production (AUTH-REM-001)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TenantContext(
                tenant_id=token[4:] or "default-tenant",
                principal_id="dev-user",
                roles=frozenset({"admin", "tenant_admin", "editor"}),
                authentication_method="dev_token",
            )

        pk = self.get_public_key()
        iss = expected_issuer or self._issuer or os.environ.get("AEGIS_JWT_ISSUER")
        aud = expected_audience or self._audience or os.environ.get("AEGIS_JWT_AUDIENCE")

        decode_options = {
            "verify_signature": True,
            "require": ["exp", "sub"],
        }
        if strict_evaluation or env == "production":
            decode_options["require"].extend(["iss", "aud"])
            decode_options["require"] = list(dict.fromkeys(decode_options["require"]))
            if not iss:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Evaluation production requires AEGIS_JWT_ISSUER (AUTH-REM-002)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not aud:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Evaluation production requires AEGIS_JWT_AUDIENCE (AUTH-REM-003)",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        decode_kwargs: Dict[str, Any] = {
            "algorithms": ["RS256"],
            "options": decode_options,
            "leeway": 30,
        }
        if iss:
            decode_kwargs["issuer"] = iss
        if aud:
            decode_kwargs["audience"] = aud

        try:
            payload = jwt.decode(token, pk, **decode_kwargs)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired (AUTH-REM-004)",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token has expired"'},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication credentials: {e}",
                headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
            )

        # Validate tenant identity
        raw_tid = payload.get("tenant_id") or payload.get("tid")
        if not raw_tid or not isinstance(raw_tid, str) or not raw_tid.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing tenant_id claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing sub claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        roles = validate_token_roles(payload)

        return TenantContext(
            tenant_id=str(raw_tid),
            principal_id=str(user_id),
            roles=roles,
            authentication_method="bearer",
        )


token_validator = EvaluationTokenValidator()
