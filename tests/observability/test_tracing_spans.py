"""OTel span no-ops when SDK absent; emits when present."""

from __future__ import annotations

from amdi.observability.tracing import span


def test_no_op_when_otel_absent() -> None:
    with span("test", foo="bar") as s:
        assert s is None
