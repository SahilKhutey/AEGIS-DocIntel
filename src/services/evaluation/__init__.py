"""src/services/evaluation package"""
from .entitlement_cache import EntitlementCache
from .entitlement_resolver import EntitlementResolver
from .entitlement_service import EntitlementService, default_entitlement_service
from .fastapi_dependencies import (
    get_entitlement_service,
    get_current_evaluation_principal,
    require_entitlement,
    verify_resource_ownership,
)
