'''
AEGIS-DocIntel / AMDI-OS — Service Container Wiring Test Suite
================================================================
Verifies that ServiceContainer initializes all 7 advanced submodules:
  - compliance_service
  - entity_service
  - versioning_service
  - anomaly_service
  - normalizer_service
  - decomposer_service
  - math_engine
'''
from __future__ import annotations

import pytest
from src.config import settings
from src.services.container import ServiceContainer


@pytest.mark.asyncio
async def test_service_container_submodules_wiring():
    container = ServiceContainer(settings)
    await container.startup()

    assert container._started is True
    assert container.compliance_service is not None
    assert container.entity_service is not None
    assert container.versioning_service is not None
    assert container.anomaly_service is not None
    assert container.normalizer_service is not None
    assert container.decomposer_service is not None
    assert container.math_engine is not None

    # Test health check
    health = await container.health_check()
    assert health["api"] == "ok"

    await container.shutdown()
