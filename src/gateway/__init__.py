"""
AEGIS-DocIntel Public Evaluation Gateway Module
PROT-FINAL-05: Workstream DEP-02
"""

from src.gateway.request_context import TrustedInternalContext
from src.gateway.service_auth import GatewayServiceAuth, service_auth_manager
from src.gateway.request_validation import RequestValidator, RequestValidationError, request_validator
from src.gateway.rate_limiting import RateLimiter, rate_limiter
from src.gateway.response_sanitizer import ResponseSanitizer, response_sanitizer
from src.gateway.upstream_client import PrivateEngineClient, UpstreamEngineError, private_engine_client

__all__ = [
    "TrustedInternalContext",
    "GatewayServiceAuth",
    "service_auth_manager",
    "RequestValidator",
    "RequestValidationError",
    "request_validator",
    "RateLimiter",
    "rate_limiter",
    "ResponseSanitizer",
    "response_sanitizer",
    "PrivateEngineClient",
    "UpstreamEngineError",
    "private_engine_client",
]
