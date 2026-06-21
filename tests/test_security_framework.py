import os
import sys
import json
import time
from pathlib import Path
import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from fastapi import FastAPI

# Configure Python path to find backend.security
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def test_security_imports():
    """Verify that all components can be imported from backend.security."""
    from backend.security import (
        SecurityEngine,
        SecurityReport,
        EncryptionManager,
        AESEncryptor,
        RSAEncryptor,
        HashManager,
        EncryptedData,
        AccessController,
        Role,
        Permission,
        Resource,
        Policy,
        AccessDecision,
        AuthenticationManager,
        AuthToken,
        User,
        APIKey,
        AuditLogger,
        AuditEvent,
        AuditEventType,
        AuditSeverity,
        SecretManager,
        Secret,
        SecretMetadata,
        SecurityMiddleware,
        RateLimiter,
        RateLimitRule,
        ThreatDetector,
        ThreatLevel,
        ThreatIndicator,
        SecurityReportData,
        SecurityMetrics,
        SecurityError,
        AuthenticationError,
        AuthorizationError,
        EncryptionError,
        SecretAccessError,
    )
    assert True


def test_exceptions():
    """Verify custom exceptions can be raised and caught."""
    from backend.security.exceptions import (
        SecurityError,
        AuthenticationError,
        AuthorizationError,
        EncryptionError,
        SecretAccessError,
        RateLimitExceededError,
        ThreatDetectedError,
    )

    with pytest.raises(SecurityError):
        raise AuthenticationError("Auth failed")

    with pytest.raises(SecurityError):
        raise AuthorizationError("Access denied")

    with pytest.raises(SecurityError):
        raise EncryptionError("Crypt failed")

    with pytest.raises(SecurityError):
        raise SecretAccessError("Secret failed")

    with pytest.raises(SecurityError):
        raise RateLimitExceededError("Rate limit exceeded")

    with pytest.raises(SecurityError):
        raise ThreatDetectedError("Threat detected")


def test_hash_compat():
    """Verify password hashing and verification."""
    from backend.security.hash_compat import hash_password, verify_password

    pw = "SecretSecurePassword123!"
    hashed = hash_password(pw)
    
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_symmetric_encryption():
    """Verify AES symmetric encryption and decryption."""
    from backend.security.encryption import AESEncryptor, EncryptionError

    encryptor = AESEncryptor()
    plaintext = "Sensitive data to encrypt"

    encrypted = encryptor.encrypt(plaintext)
    assert encrypted.ciphertext != plaintext.encode()
    assert encrypted.nonce is not None
    assert encrypted.algorithm == "AES-256-GCM"

    decrypted = encryptor.decrypt(encrypted)
    assert decrypted.decode("utf-8") == plaintext

    # Verify associated data authentication
    aad = b"associated metadata"
    encrypted_aad = encryptor.encrypt(plaintext, associated_data=aad)
    
    decrypted_aad = encryptor.decrypt(encrypted_aad, associated_data=aad)
    assert decrypted_aad.decode("utf-8") == plaintext

    # Decryption should fail with wrong AAD
    with pytest.raises(EncryptionError):
        encryptor.decrypt(encrypted_aad, associated_data=b"wrong metadata")


def test_asymmetric_encryption():
    """Verify RSA asymmetric encryption, decryption, signing, and verification."""
    from backend.security.encryption import RSAEncryptor

    encryptor = RSAEncryptor()
    plaintext = "asymmetric secret payload"

    encrypted = encryptor.encrypt(plaintext)
    assert encrypted.ciphertext != plaintext.encode()
    
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted.decode("utf-8") == plaintext

    # Verify signature
    signature = encryptor.sign(plaintext)
    assert encryptor.verify(plaintext, signature) is True
    assert encryptor.verify("different message", signature) is False


def test_encryption_manager():
    """Verify key registration, retrieval, and rotation in EncryptionManager."""
    from backend.security.encryption import EncryptionManager, EncryptionError

    mgr = EncryptionManager()
    mgr.create_aes_key("key1")
    mgr.create_aes_key("key2")
    
    plaintext = "hello world"
    encrypted = mgr.encrypt_aes(plaintext, "key1")
    assert encrypted.key_id == "key1"
    
    decrypted = mgr.decrypt_aes(encrypted)
    assert decrypted.decode("utf-8") == plaintext

    # Test key rotation
    mgr.rotate_aes_key("key1", "key3")
    assert mgr.active_aes_id == "key3"

    # Encrypting with non-existent key fails
    with pytest.raises(EncryptionError):
        mgr.encrypt_aes(plaintext, "key_invalid")


def test_access_control_rbac():
    """Verify RBAC roles, assignments, hierarchies, and permission queries."""
    from backend.security.access_control import AccessController, Role, Permission, Resource

    controller = AccessController()
    controller.create_default_roles()

    # Verify viewer role
    controller.assign_role_to_user("user_v", "viewer")
    assert Permission.READ in controller.get_user_permissions("user_v")
    assert Permission.WRITE not in controller.get_user_permissions("user_v")

    # Assign viewer role
    controller.assign_role_to_user("bob", "viewer")
    assert Permission.READ in controller.get_user_permissions("bob")
    assert Permission.WRITE not in controller.get_user_permissions("bob")

    # Verify admin role inherits parent permissions or explicitly contains all
    controller.assign_role_to_user("alice", "admin")
    alice_perms = controller.get_user_permissions("alice")
    assert Permission.READ in alice_perms
    assert Permission.WRITE in alice_perms
    assert Permission.DELETE in alice_perms
    assert Permission.ADMIN in alice_perms

    # Custom role with parent roles
    custom_role = Role("developer", permissions={Permission.EXECUTE}, parent_roles=["editor"])
    controller.add_role(custom_role)
    controller.assign_role_to_user("dev_user", "developer")

    dev_perms = controller.get_user_permissions("dev_user")
    assert Permission.EXECUTE in dev_perms
    assert Permission.READ in dev_perms  # from editor
    assert Permission.WRITE in dev_perms  # from editor
    assert Permission.DELETE not in dev_perms


def test_access_control_abac():
    """Verify ABAC policy evaluation."""
    from backend.security.access_control import AccessController, Permission, Resource, Policy

    controller = AccessController()
    
    # Register resource owned by owner_1
    res = Resource(resource_id="doc_1", resource_type="document", owner_id="owner_1")
    controller.register_resource(res)

    # ABAC rule: grant access if request is made during working hours (9 AM - 5 PM)
    def work_hours_policy(user_attrs, resource, action, context):
        hour = context.get("hour", 0)
        return 9 <= hour <= 17

    policy = Policy(
        name="work_hours",
        description="Access allowed only during work hours",
        predicate=work_hours_policy,
        priority=10
    )
    controller.add_policy(policy)

    # Access inside working hours
    dec1 = controller.check_access("user_1", res, Permission.READ, {"hour": 10})
    assert dec1.granted is True

    # Access outside working hours
    dec2 = controller.check_access("user_1", res, Permission.READ, {"hour": 22})
    assert dec2.granted is False


def test_authentication_jwt():
    """Verify authentication managerJWT issuance, verification, and revocation."""
    from backend.security.authentication import AuthenticationManager, AuthenticationError

    mgr = AuthenticationManager()
    
    # Create user
    user = mgr.create_user("john_doe", "john@example.com", "johnspassword")
    assert user.username == "john_doe"
    assert user.password_hash is not None

    # Authenticate
    token = mgr.authenticate_password("john_doe", "johnspassword")
    assert token.username == "john_doe"
    assert not token.is_expired()

    # Verify token
    verified = mgr.verify_token(token.token)
    assert verified.user_id == user.user_id
    assert verified.username == "john_doe"

    # Revoke token
    # Extract JTI from JWT payload
    parts = token.token.split(".")
    payload = json.loads(AuthenticationManager._b64url_decode(parts[1]))
    jti = payload["jti"]
    
    mgr.revoke_token(jti)
    with pytest.raises(AuthenticationError):
        mgr.verify_token(token.token)


def test_authentication_api_keys():
    """Verify API Key creation, verification, and revocation."""
    from backend.security.authentication import AuthenticationManager, AuthenticationError

    mgr = AuthenticationManager()
    user = mgr.create_user("app_server", "app@example.com", "serverpassword")

    # Issue API Key
    raw_key, api_key = mgr.create_api_key(user.user_id, "Prod Server Key", scopes=["read"])
    assert raw_key.startswith("prod_server_key") is False  # secure random
    assert api_key.key_id in user.api_keys

    # Verify API Key
    token = mgr.verify_api_key(raw_key)
    assert token.user_id == user.user_id
    assert "read" in token.scopes

    # Revoke key
    mgr.revoke_api_key(api_key.key_id)
    with pytest.raises(AuthenticationError):
        mgr.verify_api_key(raw_key)


def test_audit_logging():
    """Verify tamper-evident audit logging functionality."""
    from backend.security.audit_log import AuditLogger, AuditEventType, AuditSeverity

    logger = AuditLogger()
    
    # Log events
    logger.log(
        event_type=AuditEventType.LOGIN_SUCCESS,
        actor_id="user_1",
        resource_type="session",
        resource_id="login_endpoint",
        action="login",
        outcome="success"
    )

    logger.log(
        event_type=AuditEventType.SECRET_ACCESSED,
        actor_id="user_1",
        resource_type="secret",
        resource_id="db_password",
        action="read",
        outcome="success",
        severity=AuditSeverity.WARNING
    )

    # Chain validation should be valid
    assert logger.verify_chain() is True

    # Tamper with an event in the chain
    event = logger.events[0]
    event.action = "delete"  # modify action post-hoc

    # Verification should fail
    assert logger.verify_chain() is False


def test_secret_manager():
    """Verify Vault-like secret manager versioning, permissions, and rotation."""
    from backend.security import SecurityEngine
    from backend.security.exceptions import SecretAccessError

    engine = SecurityEngine()
    
    # Register access controller roles
    engine.access_control.assign_role_to_user("bob", "viewer")
    engine.access_control.assign_role_to_user("alice", "admin")

    # Create secret owned by alice
    secret = engine.secret_manager.create_secret(
        secret_id="openai_api_key",
        value="sk-1234567890",
        owner="alice",
        name="OpenAI API Key"
    )
    assert secret.metadata.version == 1

    # Viewer bob tries to read secret, access denied
    with pytest.raises(SecretAccessError):
        engine.secret_manager.get_secret("openai_api_key", "bob")

    # Admin alice reads secret successfully
    val = engine.secret_manager.get_secret("openai_api_key", "alice")
    assert val == "sk-1234567890"

    # Update secret to new version
    engine.secret_manager.update_secret("openai_api_key", "sk-new-value", "alice")
    assert engine.secret_manager.secrets["openai_api_key"].metadata.version == 2
    assert len(engine.secret_manager.secrets["openai_api_key"].previous_versions) == 1

    # Rotate secret
    rotated = engine.secret_manager.rotate_secret("openai_api_key", "alice")
    assert rotated.metadata.version == 3


def test_rate_limiter():
    """Verify sliding window rate limiting."""
    from backend.security.rate_limiter import RateLimiter, RateLimitRule
    from backend.security.exceptions import RateLimitExceededError

    limiter = RateLimiter()
    rule = RateLimitRule(key="api", limit=3, window_seconds=2)
    limiter.add_rule("limit_3_2s", rule)

    # Send 3 requests (should be allowed)
    limiter.check_rate_limit("limit_3_2s", "client_1")
    limiter.check_rate_limit("limit_3_2s", "client_1")
    limiter.check_rate_limit("limit_3_2s", "client_1")

    # 4th request should raise RateLimitExceededError
    with pytest.raises(RateLimitExceededError):
        limiter.check_rate_limit("limit_3_2s", "client_1")

    # Sleep for window to expire
    time.sleep(2.1)

    # Request should be allowed again
    limiter.check_rate_limit("limit_3_2s", "client_1")


def test_threat_detector():
    """Verify SQLi, XSS, and Path Traversal detection."""
    from backend.security.threat_detector import ThreatDetector, ThreatLevel
    from backend.security.exceptions import ThreatDetectedError

    detector = ThreatDetector()

    # SQL Injection
    sqli = "SELECT * FROM users WHERE username = 'admin' UNION SELECT password FROM users--"
    sqli_threats = detector.scan_text(sqli)
    assert len(sqli_threats) > 0
    assert sqli_threats[0].indicator_type == "sql_injection"

    # XSS
    xss = "<script>alert('hack')</script>"
    xss_threats = detector.scan_text(xss)
    assert len(xss_threats) > 0
    assert xss_threats[0].indicator_type == "xss"

    # Path Traversal
    traversal = "../../../../etc/passwd"
    traversal_threats = detector.scan_text(traversal)
    assert len(traversal_threats) > 0
    assert traversal_threats[0].indicator_type == "path_traversal"
    assert traversal_threats[0].severity == ThreatLevel.CRITICAL

    # Safe text
    safe = "This is a safe sentence about regular activities."
    assert len(detector.scan_text(safe)) == 0

    # block check raises exception
    with pytest.raises(ThreatDetectedError):
        detector.check_threats(path="/api/documents", query_params={"file": traversal})


def test_security_middleware():
    """Verify security middleware controls on a mock FastAPI application."""
    from backend.security import SecurityEngine, RateLimitRule, SecurityMiddleware
    
    engine = SecurityEngine()
    
    # Configure a rate limit rule for global api
    engine.rate_limiter.add_rule(
        "global_api",
        RateLimitRule(key="global", limit=2, window_seconds=60)
    )

    # Setup user
    user = engine.authentication.create_user("alice", "alice@example.com", "password")
    token = engine.authentication.create_token(user)

    app = FastAPI()
    app.add_middleware(SecurityMiddleware, security_engine=engine)

    @app.get("/test")
    def test_route():
        return {"status": "ok"}

    @app.post("/test-post")
    def test_post_route():
        return {"status": "post_ok"}

    client = TestClient(app)

    # 1. Accessing without auth header fails
    response = client.get("/test")
    assert response.status_code == 401

    # 2. Accessing with invalid token fails
    response = client.get("/test", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

    # 3. Accessing with valid token succeeds
    headers = {"Authorization": f"Bearer {token.token}"}
    response = client.get("/test", headers=headers)
    assert response.status_code == 200

    # 4. Trigger rate limit (rule allows 2 requests)
    # This is request #2 (first success was #1)
    response = client.get("/test", headers=headers)
    assert response.status_code == 200

    # This is request #3 -> rate limited
    response = client.get("/test", headers=headers)
    assert response.status_code == 429

    # Reset rate limit for next test
    engine.rate_limiter.reset_limit("global_api", user.user_id)

    # 5. Access with threat fails
    response = client.get("/test?param=../../etc/passwd", headers=headers)
    assert response.status_code == 400


def test_security_engine_and_reporting():
    """Verify the SecurityEngine orchestrator and report compilation."""
    from backend.security import SecurityEngine, SecurityReport, AuditEventType

    engine = SecurityEngine()
    
    # Perform some mock operations
    user = engine.authentication.create_user("admin_user", "admin@example.com", "pass")
    token = engine.authentication.create_token(user)

    # Verify audit logs record user actions
    engine.audit_log.log(
        event_type=AuditEventType.CONFIG_CHANGE,
        actor_id=user.user_id,
        resource_type="report",
        resource_id="main",
        action="generate",
        outcome="success"
    )

    # Retrieve report
    report = engine.generate_report()
    assert report.status == "secure"
    assert report.metrics.total_requests == 0  # not via middleware here
    assert report.metrics.active_users == 1
