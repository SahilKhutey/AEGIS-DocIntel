"""
AEGIS-DocIntel — Webhook Security & SSRF Protection
===================================================
Enforces enterprise outbound security controls:
- Strict SSRF (Server-Side Request Forgery) protection against internal networks,
  loopback addresses, link-local addresses, and cloud metadata services.
- Cryptographic HMAC-SHA256 signature creation and verification.
- Timestamp freshness validation to prevent replay attacks.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import socket
import time
from urllib.parse import urlparse
from typing import Tuple, List
import structlog

log = structlog.get_logger("aegis.security.webhooks")

# Default tolerance window for webhook signatures (5 minutes)
DEFAULT_TIMESTAMP_TOLERANCE_SECONDS = 300

# Cloud metadata IP addresses to explicitly block
BLOCKED_CLOUD_METADATA_IPS = {
    ipaddress.ip_address("169.254.169.254"),  # AWS/GCP/Azure/OpenStack metadata
    ipaddress.ip_address("fd00:ec2::254"),     # AWS IPv6 metadata
}


def is_safe_webhook_url(url: str, allow_private_for_tests: bool = False) -> Tuple[bool, str]:
    """
    Validate that a destination URL is safe to dispatch webhooks to.
    Blocks:
    - Non-http / non-https schemes
    - Loopback IPs (127.0.0.0/8, ::1)
    - Link-local IPs (169.254.0.0/16, fe80::/10)
    - Cloud metadata services (169.254.169.254)
    - Private RFC 1918 / RFC 4193 networks (unless allow_private_for_tests=True)
    - Unspecified, multicast, and reserved addresses
    """
    if not url:
        return False, "Webhook URL cannot be empty"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid scheme '{parsed.scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Webhook URL must include a valid hostname"

    # Block localhost explicitly by name
    if hostname.lower() in ("localhost", "localhost.localdomain"):
        if not allow_private_for_tests:
            return False, "Localhost destinations are forbidden"

    # Resolve IP addresses for hostname
    try:
        resolved_addrs = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        return False, f"Cannot resolve destination hostname '{hostname}': {e}"
    except Exception as e:
        return False, f"DNS resolution failed: {e}"

    if not resolved_addrs:
        return False, f"No IP addresses resolved for hostname '{hostname}'"

    for addr_info in resolved_addrs:
        ip_str = addr_info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid IP address format: {ip_str}"

        # 1. Cloud metadata check
        if ip in BLOCKED_CLOUD_METADATA_IPS:
            return False, f"Destination IP {ip} is a forbidden cloud metadata service"

        # 2. Loopback check
        if ip.is_loopback:
            if not allow_private_for_tests:
                return False, f"Destination IP {ip} is a loopback address"

        # 3. Link-local check
        if ip.is_link_local:
            return False, f"Destination IP {ip} is a link-local address"

        # 4. Multicast or unspecified
        if ip.is_multicast or ip.is_unspecified:
            return False, f"Destination IP {ip} is not a valid unicast address"

        # 5. Private network check
        if ip.is_private:
            if not allow_private_for_tests:
                return False, f"Destination IP {ip} is within a private network range"

        # 6. Reserved
        if ip.is_reserved:
            return False, f"Destination IP {ip} is a reserved IP address"

    return True, ""


def generate_webhook_signature(payload_bytes: bytes, secret: str, timestamp: int) -> str:
    """
    Generate an HMAC-SHA256 signature for a webhook payload.
    The signed payload is '{timestamp}.{payload_bytes}'.
    """
    if not secret:
        raise ValueError("Webhook secret is required for signing")
    message = f"{timestamp}.".encode("utf-8") + payload_bytes
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_webhook_signature(
    payload_bytes: bytes,
    secret: str,
    signature: str,
    timestamp: int,
    tolerance_seconds: int = DEFAULT_TIMESTAMP_TOLERANCE_SECONDS,
    now: float = None,
) -> bool:
    """
    Verify an HMAC-SHA256 webhook signature and timestamp freshness.
    Returns True if valid, False otherwise.
    """
    if not secret or not signature:
        return False

    current_time = now if now is not None else time.time()
    # Check timestamp freshness (replay attack prevention)
    if abs(current_time - timestamp) > tolerance_seconds:
        log.warning("Webhook timestamp outside tolerance window", timestamp=timestamp, now=current_time)
        return False

    expected_signature = generate_webhook_signature(payload_bytes, secret, timestamp)
    return hmac.compare_digest(expected_signature, signature)
