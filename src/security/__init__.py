"""src/security package"""
from .event_schema import SecurityEvent, Severity
from .event_catalog import is_known_event_type, get_default_severity, EVENT_TAXONOMY
from .event_redaction import redact_text, sanitize_event_details, contains_sensitive_data
from .audit_integrity import (
    GENESIS_HASH,
    canonical_event_bytes,
    calculate_event_hash,
    verify_chain,
    create_checkpoint,
    verify_checkpoint,
)
from .security_context import (
    SecurityContext,
    get_current_security_context,
    set_current_security_context,
    reset_security_context,
)
from .private_engine_guard import (
    EngineAuthContext,
    PrivateEngineGuard,
    private_engine_guard,
)
