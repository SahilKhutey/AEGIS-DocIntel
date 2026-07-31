"""structlog produces valid JSON when AMDI_LOG_JSON is set."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from amdi.config import get_settings
from amdi.observability.logging import configure, get_logger


def test_structlog_json_emitted(monkeypatch) -> None:
    monkeypatch.setenv("AMDI_LOG_JSON", "1")
    get_settings.cache_clear()
    configure()
    buf = io.StringIO()
    with redirect_stdout(buf):
        get_logger("test").info("hello", n=42)
    line = buf.getvalue().strip()
    rec = json.loads(line)
    assert rec["event"] == "hello"
    assert rec["n"] == 42
