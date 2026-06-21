import os
import sys
from pathlib import Path
import pytest

def switch_env(target: str):
    # Resolve absolute paths
    root_dir = str(Path(__file__).parent.parent.resolve())
    amdi_dir = str((Path(__file__).parent.parent / "amdi-os").resolve())

    # Update sys.path
    if target == 'amdi-os':
        # Prioritize amdi_dir for src imports, but keep root_dir for dashboard etc.
        sys.path = [p for p in sys.path if p != amdi_dir]
        sys.path.insert(0, amdi_dir)
        if root_dir not in sys.path:
            sys.path.append(root_dir)
    else:
        # Strictly prioritize root_dir and exclude amdi_dir
        sys.path = [p for p in sys.path if p not in (root_dir, amdi_dir)]
        sys.path.insert(0, root_dir)

    # Check the path of currently loaded 'src' module
    current_src_path = None
    if 'src' in sys.modules:
        src_mod = sys.modules['src']
        if hasattr(src_mod, '__file__') and src_mod.__file__:
            current_src_path = os.path.abspath(src_mod.__file__)

    expect_amdi = (target == 'amdi-os')
    is_amdi = current_src_path and ("amdi-os" in current_src_path)

    # If there is a mismatch, unload 'src' and all its submodules
    if current_src_path and (is_amdi != expect_amdi):
        to_delete = [name for name in sys.modules if name == "src" or name.startswith("src.")]
        for name in to_delete:
            del sys.modules[name]

def pytest_runtest_setup(item):
    filename = item.fspath.basename
    if filename in ("test_aegis.py", "test_dashboard.py"):
        switch_env("root")
    else:
        switch_env("amdi-os")
