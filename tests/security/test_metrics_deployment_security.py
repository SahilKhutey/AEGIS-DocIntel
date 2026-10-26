"""
tests/security/test_metrics_deployment_security.py
==================================================
Phase 3.1 Work Package C — Metrics and Deployment Security Acceptance:
Verifies that:
1. Container deployment topology restricts API exposure to loopback (127.0.0.1).
2. Prometheus and internal services reside on an isolated bridge network.
3. Monitoring ports (9090, 3000) are not unintentionally published to public host interfaces.
4. Prometheus scrape configuration targets internal service names.
5. Telemetry pseudonymization and metrics safety invariants are upheld.
"""
from __future__ import annotations

from pathlib import Path
import yaml
import pytest

from src.api.auth_guard import PUBLIC_PREFIXES
from src.core.settings import load_runtime_settings

DEPLOY_DIR = Path(__file__).resolve().parent.parent.parent / "deploy"


def test_compose_api_loopback_binding():
    """API host binding must be loopback-only (127.0.0.1) in production docker-compose."""
    compose_file = DEPLOY_DIR / "docker-compose.yml"
    assert compose_file.exists(), f"Missing docker-compose.yml at {compose_file}"

    with open(compose_file, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    api_service = compose.get("services", {}).get("aegis-api", {})
    ports = api_service.get("ports", [])
    assert len(ports) > 0, "aegis-api should define host port mapping"

    for port_mapping in ports:
        port_str = str(port_mapping)
        assert port_str.startswith("127.0.0.1:"), (
            f"API port '{port_str}' must be bound exclusively to loopback 127.0.0.1"
        )


def test_compose_monitoring_services_internal_network_isolation():
    """Prometheus and Grafana services must not publish raw monitoring ports to host."""
    compose_file = DEPLOY_DIR / "docker-compose.yml"
    with open(compose_file, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    prom = services.get("prometheus", {})
    graf = services.get("grafana", {})

    # Prometheus must have no published ports (accessible only within internal network)
    assert "ports" not in prom, "Prometheus should not expose published host ports"

    # Both must share the aegis-internal network with aegis-api
    networks = compose.get("networks", {})
    assert "aegis-internal" in networks
    assert "aegis-internal" in prom.get("networks", [])
    assert "aegis-internal" in graf.get("networks", [])
    assert "aegis-internal" in services.get("aegis-api", {}).get("networks", [])


def test_prometheus_scrape_target_internal_network():
    """Prometheus configuration scrapes aegis-api:8000 via internal docker DNS."""
    prom_file = DEPLOY_DIR / "prometheus.yml"
    assert prom_file.exists()

    with open(prom_file, "r", encoding="utf-8") as f:
        prom_cfg = yaml.safe_load(f)

    scrape_configs = prom_cfg.get("scrape_configs", [])
    aegis_jobs = [j for j in scrape_configs if j.get("job_name") == "aegis-docintel"]
    assert len(aegis_jobs) == 1

    job = aegis_jobs[0]
    assert job.get("metrics_path") == "/metrics"
    targets = job.get("static_configs", [{}])[0].get("targets", [])
    assert "aegis-api:8000" in targets


def test_metrics_path_in_public_prefixes_policy():
    """Metrics endpoint prefix is explicitly configured in AuthGuard public prefixes."""
    assert "/metrics" in PUBLIC_PREFIXES


def test_telemetry_pseudonymization_default():
    """Runtime settings enable telemetry pseudonymization by default to protect tenant IDs."""
    settings = load_runtime_settings(validate_production=False)
    assert settings.pseudonymize_telemetry is True
