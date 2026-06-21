"""
Secret Management
==================

Vault-like secret storage with encryption, versioning, and access control.

Features:
    - Encrypted at rest (AES-256-GCM)
    - Versioned (history of changes)
    - Access-controlled (per-secret policies)
    - Auto-rotation support
    - Audit-logged
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .access_control import AccessController, Permission, Resource, Policy
from .audit_log import AuditEventType, AuditLogger, AuditSeverity
from .encryption import EncryptionManager, EncryptedData
from .exceptions import SecretAccessError, AuthorizationError


@dataclass
class SecretMetadata:
    """Metadata for a secret."""

    secret_id: str
    name: str
    version: int
    created_at: float
    updated_at: float
    created_by: str
    rotation_interval_days: Optional[int] = None
    last_rotated: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class Secret:
    """A secret with metadata and value (encrypted)."""

    metadata: SecretMetadata
    encrypted_value: bytes
    nonce: bytes
    previous_versions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metadata": {
                "secret_id": self.metadata.secret_id,
                "name": self.metadata.name,
                "version": self.metadata.version,
                "created_at": self.metadata.created_at,
                "updated_at": self.metadata.updated_at,
                "created_by": self.metadata.created_by,
                "rotation_interval_days": self.metadata.rotation_interval_days,
                "tags": self.metadata.tags,
                "description": self.metadata.description,
            },
            "num_versions": len(self.previous_versions) + 1,
        }


class SecretManager:
    """
    Secure secret storage and retrieval.

    Usage:
        mgr = SecretManager(encryption_manager, access_controller, audit_logger)
        mgr.create_secret("api_key_openai", "sk-...", owner="admin")
        value = mgr.get_secret("api_key_openai", accessor="alice")
    """

    def __init__(
        self,
        encryption_manager: EncryptionManager,
        access_controller: AccessController,
        audit_logger: AuditLogger,
        master_key_id: str = "master",
    ) -> None:
        # ensure master key exists
        if master_key_id not in encryption_manager.aes_keys:
            encryption_manager.create_aes_key(master_key_id)
        self.encryption_manager = encryption_manager
        self.access_controller = access_controller
        self.audit_logger = audit_logger
        self.master_key_id = master_key_id
        self.secrets: Dict[str, Secret] = {}

        # Register default policy: Admins can access any secret
        admin_policy = Policy(
            name="admin_secret_override",
            description="Admins can access any secret",
            predicate=lambda user_attrs, resource, action, context: context.get("is_admin", False),
            priority=100
        )
        self.access_controller.add_policy(admin_policy)

    def create_secret(
        self,
        secret_id: str,
        value: str,
        owner: str,
        name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        description: str = "",
        rotation_interval_days: Optional[int] = None,
    ) -> Secret:
        """Create and store a new secret."""
        if secret_id in self.secrets:
            raise SecretAccessError(f"Secret '{secret_id}' already exists")

        # 1. Register resource with access controller (restrict permissions to ADMIN)
        resource = Resource(
            resource_id=secret_id,
            resource_type="secret",
            owner_id=owner,
            permissions={Permission.ADMIN}
        )
        self.access_controller.register_resource(resource)

        # 2. Encrypt value
        encrypted = self.encryption_manager.encrypt_aes(value, self.master_key_id)

        # 3. Create secret
        now = time.time()
        metadata = SecretMetadata(
            secret_id=secret_id,
            name=name or secret_id,
            version=1,
            created_at=now,
            updated_at=now,
            created_by=owner,
            rotation_interval_days=rotation_interval_days,
            last_rotated=now,
            tags=tags or {},
            description=description,
        )
        secret = Secret(
            metadata=metadata,
            encrypted_value=encrypted.ciphertext,
            nonce=encrypted.nonce,
        )

        self.secrets[secret_id] = secret

        # 4. Audit Log
        self.audit_logger.log(
            event_type=AuditEventType.SECRET_ACCESSED,
            actor_id=owner,
            resource_type="secret",
            resource_id=secret_id,
            action="create",
            outcome="success",
            details={"name": metadata.name}
        )

        return secret

    def get_secret(self, secret_id: str, accessor: str) -> str:
        """Retrieve and decrypt secret value."""
        if secret_id not in self.secrets:
            raise SecretAccessError(f"Secret '{secret_id}' not found")

        secret = self.secrets[secret_id]
        resource = self.access_controller.resources.get(secret_id)
        
        # Check permissions
        if resource:
            user_perms = self.access_controller.get_user_permissions(accessor)
            context = {"is_admin": Permission.ADMIN in user_perms}
            try:
                self.access_controller.require_access(accessor, resource, Permission.READ, context)
            except AuthorizationError as exc:
                self.audit_logger.log(
                    event_type=AuditEventType.SECRET_ACCESSED,
                    actor_id=accessor,
                    resource_type="secret",
                    resource_id=secret_id,
                    action="read",
                    outcome="denied",
                    severity=AuditSeverity.WARNING,
                    details={"reason": str(exc)}
                )
                raise SecretAccessError(f"Access denied to secret '{secret_id}': {exc}") from exc

        # Decrypt
        try:
            encrypted = EncryptedData(
                ciphertext=secret.encrypted_value,
                nonce=secret.nonce,
                key_id=self.master_key_id
            )
            decrypted = self.encryption_manager.decrypt_aes(encrypted)
            
            self.audit_logger.log(
                event_type=AuditEventType.SECRET_ACCESSED,
                actor_id=accessor,
                resource_type="secret",
                resource_id=secret_id,
                action="read",
                outcome="success"
            )
            return decrypted.decode("utf-8")
        except Exception as exc:
            raise SecretAccessError(f"Failed to decrypt secret '{secret_id}': {exc}") from exc

    def update_secret(self, secret_id: str, value: str, accessor: str) -> Secret:
        """Update a secret and create a new version."""
        if secret_id not in self.secrets:
            raise SecretAccessError(f"Secret '{secret_id}' not found")

        secret = self.secrets[secret_id]
        resource = self.access_controller.resources.get(secret_id)

        # Check permissions
        if resource:
            user_perms = self.access_controller.get_user_permissions(accessor)
            context = {"is_admin": Permission.ADMIN in user_perms}
            try:
                self.access_controller.require_access(accessor, resource, Permission.WRITE, context)
            except AuthorizationError as exc:
                self.audit_logger.log(
                    event_type=AuditEventType.SECRET_ACCESSED,
                    actor_id=accessor,
                    resource_type="secret",
                    resource_id=secret_id,
                    action="update",
                    outcome="denied",
                    severity=AuditSeverity.WARNING,
                    details={"reason": str(exc)}
                )
                raise SecretAccessError(f"Access denied to update secret '{secret_id}': {exc}") from exc

        # Save previous version
        prev_ver = {
            "version": secret.metadata.version,
            "encrypted_value": secret.encrypted_value,
            "nonce": secret.nonce,
            "updated_at": secret.metadata.updated_at,
        }
        secret.previous_versions.append(prev_ver)

        # Encrypt new value
        encrypted = self.encryption_manager.encrypt_aes(value, self.master_key_id)

        # Update metadata and secret
        now = time.time()
        secret.metadata.version += 1
        secret.metadata.updated_at = now
        secret.encrypted_value = encrypted.ciphertext
        secret.nonce = encrypted.nonce

        self.audit_logger.log(
            event_type=AuditEventType.SECRET_ACCESSED,
            actor_id=accessor,
            resource_type="secret",
            resource_id=secret_id,
            action="update",
            outcome="success",
            details={"version": secret.metadata.version}
        )

        return secret

    def delete_secret(self, secret_id: str, accessor: str) -> None:
        """Delete a secret and clean up resources."""
        if secret_id not in self.secrets:
            raise SecretAccessError(f"Secret '{secret_id}' not found")

        resource = self.access_controller.resources.get(secret_id)

        # Check permissions
        if resource:
            user_perms = self.access_controller.get_user_permissions(accessor)
            context = {"is_admin": Permission.ADMIN in user_perms}
            try:
                self.access_controller.require_access(accessor, resource, Permission.DELETE, context)
            except AuthorizationError as exc:
                self.audit_logger.log(
                    event_type=AuditEventType.SECRET_ACCESSED,
                    actor_id=accessor,
                    resource_type="secret",
                    resource_id=secret_id,
                    action="delete",
                    outcome="denied",
                    severity=AuditSeverity.WARNING,
                    details={"reason": str(exc)}
                )
                raise SecretAccessError(f"Access denied to delete secret '{secret_id}': {exc}") from exc

        # Perform deletion
        del self.secrets[secret_id]
        if secret_id in self.access_controller.resources:
            del self.access_controller.resources[secret_id]

        self.audit_logger.log(
            event_type=AuditEventType.SECRET_ACCESSED,
            actor_id=accessor,
            resource_type="secret",
            resource_id=secret_id,
            action="delete",
            outcome="success"
        )

    def rotate_secret(self, secret_id: str, accessor: str, new_value: Optional[str] = None) -> Secret:
        """Rotate secret (re-encrypt with new active key or update to new value)."""
        if secret_id not in self.secrets:
            raise SecretAccessError(f"Secret '{secret_id}' not found")

        # In this implementation, rotation checks WRITE access and updates last_rotated.
        # If new_value is not provided, we re-encrypt the old value under the active master key id.
        old_val = self.get_secret(secret_id, accessor)
        val_to_use = new_value if new_value is not None else old_val

        secret = self.update_secret(secret_id, val_to_use, accessor)
        secret.metadata.last_rotated = time.time()

        self.audit_logger.log(
            event_type=AuditEventType.SECRET_ACCESSED,
            actor_id=accessor,
            resource_type="secret",
            resource_id=secret_id,
            action="rotate",
            outcome="success"
        )
        return secret

    def list_secrets(self, accessor: str) -> List[SecretMetadata]:
        """List metadata of secrets that the accessor has permission to read."""
        results = []
        for secret_id, secret in self.secrets.items():
            resource = self.access_controller.resources.get(secret_id)
            if resource:
                # If access check succeeds, include in list
                decision = self.access_controller.check_access(accessor, resource, Permission.READ)
                if decision.granted:
                    results.append(secret.metadata)
        return results
