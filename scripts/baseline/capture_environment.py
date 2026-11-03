#!/usr/bin/env python3
"""
scripts/baseline/capture_environment.py
=======================================
Captures OS, hardware, language runtimes, package listings, and non-sensitive env vars.
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
ENV_DIR = ROOT / "audit" / "baseline" / "environment"
ENV_DIR.mkdir(parents=True, exist_ok=True)


def get_cmd_output(cmd: list[str]) -> str:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception as e:
        return f"UNAVAILABLE ({e})"


def capture_system_info() -> dict[str, str]:
    info = {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "machine": platform.machine(),
    }
    # On Windows, try to get CPU cores and RAM via PowerShell
    if platform.system() == "Windows":
        try:
            ps_cpu = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"],
                capture_output=True, text=True
            )
            if ps_cpu.returncode == 0 and ps_cpu.stdout.strip():
                info["cpu_name"] = ps_cpu.stdout.strip().splitlines()[0]
        except Exception:
            pass

        try:
            ps_mem = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "[math]::Round((Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum).Sum / 1GB, 2)"],
                capture_output=True, text=True
            )
            if ps_mem.returncode == 0 and ps_mem.stdout.strip():
                info["total_ram_gb"] = f"{ps_mem.stdout.strip()} GB"
        except Exception:
            pass

    return info


def capture_runtimes() -> dict[str, str]:
    runtimes = {
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "pip": get_cmd_output([sys.executable, "-m", "pip", "--version"]),
        "git": get_cmd_output(["git", "--version"]),
    }
    
    if shutil.which("node"):
        runtimes["node"] = get_cmd_output(["node", "--version"])
    else:
        runtimes["node"] = "NOT INSTALLED"
        
    if shutil.which("npm"):
        runtimes["npm"] = get_cmd_output(["npm", "--version"])
    else:
        runtimes["npm"] = "NOT INSTALLED"

    return runtimes


def main() -> int:
    try:
        sys_info = capture_system_info()
        runtimes = capture_runtimes()

        # 1. System information text
        sys_txt = "\n".join(f"{k}: {v}" for k, v in sys_info.items())
        (ENV_DIR / "system_information.txt").write_text(sys_txt + "\n", encoding="utf-8")

        # 2. Runtime versions text
        run_txt = "\n".join(f"{k}: {v}" for k, v in runtimes.items())
        (ENV_DIR / "runtime_versions.txt").write_text(run_txt + "\n", encoding="utf-8")

        # 3. Installed packages JSON
        pip_list_proc = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True
        )
        packages = []
        if pip_list_proc.returncode == 0:
            try:
                packages = json.loads(pip_list_proc.stdout)
            except json.JSONDecodeError:
                pass
        (ENV_DIR / "installed_packages.json").write_text(
            json.dumps(packages, indent=2), encoding="utf-8"
        )

        # 4. Pip check (health)
        pip_check_proc = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True, text=True
        )
        health_data = {
            "status": "PASS" if pip_check_proc.returncode == 0 else "CONFLICTS_DETECTED",
            "returncode": pip_check_proc.returncode,
            "stdout": pip_check_proc.stdout.strip(),
            "stderr": pip_check_proc.stderr.strip(),
            "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        (ENV_DIR / "dependency_health.json").write_text(
            json.dumps(health_data, indent=2), encoding="utf-8"
        )

        # 5. Environment variables (NAMES ONLY, strictly NO secrets)
        env_names = sorted(list(os.environ.keys()))
        (ENV_DIR / "environment_variables_inventory.txt").write_text(
            "\n".join(env_names) + "\n", encoding="utf-8"
        )

        # 6. Environment manifest JSON
        manifest = {
            "baseline_id": "AEGIS-BASELINE-001",
            "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "operating_system": {
                "name": sys_info.get("os_name"),
                "release": sys_info.get("os_release"),
                "architecture": sys_info.get("architecture"),
                "platform": sys_info.get("platform")
            },
            "hardware": {
                "processor": sys_info.get("processor"),
                "cpu_name": sys_info.get("cpu_name", "N/A"),
                "total_ram_gb": sys_info.get("total_ram_gb", "N/A")
            },
            "runtimes": {
                "python": {
                    "version": runtimes.get("python"),
                    "executable": runtimes.get("python_executable")
                },
                "pip": {
                    "version": runtimes.get("pip")
                },
                "node": {
                    "version": runtimes.get("node")
                },
                "npm": {
                    "version": runtimes.get("npm")
                },
                "git": {
                    "version": runtimes.get("git")
                }
            },
            "dependency_summary": {
                "installed_package_count": len(packages),
                "dependency_health_status": health_data["status"]
            }
        }
        (ENV_DIR / "environment_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        print(f"[OK] Wrote environment captures under: {ENV_DIR}")
        return 0
    except Exception as e:
        print(f"[ERROR] capture_environment failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
