"""OpenTelemetry tracing — safe to import when OTel SDK isn't installed."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

try:
    from opentelemetry import trace  # type: ignore
except ImportError:
    trace = None


_TRACER = trace.get_tracer("amdi") if trace is not None else None


@contextmanager
def span(name: str, **attrs) -> Iterator[object]:
    if _TRACER is None:
        yield None
        return
    with _TRACER.start_as_current_span(name) as s:
        for k, v in attrs.items():
            try:
                s.set_attribute(str(k), str(v))
            except Exception:  # noqa: BLE001
                pass
        yield s


__all__ = ["span"]
