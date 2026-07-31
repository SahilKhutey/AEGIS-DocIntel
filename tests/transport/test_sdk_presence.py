"""Each of the four SDK directories is non-empty and has its expected entry point."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("entry", [
    "sdks/python/src/amdi_sdk/client.py",
    "sdks/typescript/src/index.ts",
    "sdks/java/src/main/java/io/amdi/sdk/AmdiClient.java",
    "sdks/cpp/src/amdi_client.cpp",
])
def test_sdk_entry_present(entry: str) -> None:
    assert Path(entry).exists()
