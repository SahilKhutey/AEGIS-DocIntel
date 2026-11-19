"""
AEGIS-DocIntel Client Application Launcher & Process Supervisor
==============================================================
Manages startup, prerequisite verification, port negotiation, health checks,
process supervision, and zero-orphan graceful teardown.
"""
from __future__ import annotations

import atexit
import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aegis.launcher")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class LauncherError(Exception):
    pass


class ClientLauncher:
    """Supervises local standalone server and proxy processes."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or ROOT_DIR
        self.config = self._load_config()
        self.child_processes: List[subprocess.Popen] = []
        atexit.register(self.shutdown)

    def _load_config(self) -> Dict[str, Any]:
        cfg_file = self.root_dir / "config" / "client.json"
        if not cfg_file.exists():
            cfg_file = self.root_dir / "config" / "defaults.json"
        if not cfg_file.exists():
            raise LauncherError(f"Missing client configuration: {cfg_file}")
        with open(cfg_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def verify_installation_integrity(self) -> bool:
        """Verify presence of essential client artifacts."""
        required_paths = [
            self.root_dir / "keys" / "license-verification-public.pem",
            self.root_dir / "licenses" / "LICENSE",
            self.root_dir / "licenses" / "THIRD_PARTY_NOTICES.txt",
            self.root_dir / "docs" / "QUICK_START.md",
        ]
        missing = [str(p) for p in required_paths if not p.exists()]
        if missing:
            raise LauncherError(f"Installation integrity check failed. Missing files: {missing}")
        return True

    def find_free_port(self, preferred_port: int, bind_addr: str = "127.0.0.1") -> int:
        """Check if preferred port is free; if not, find the next available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((bind_addr, preferred_port))
                return preferred_port
            except OSError:
                pass
        # Bind to port 0 to get an ephemeral free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((bind_addr, 0))
            return s.getsockname()[1]

    def wait_for_health(self, url: str, timeout_seconds: int = 15) -> bool:
        """Poll health check endpoint until HTTP 200 or timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                with urllib.request.urlopen(url, timeout=1.0) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                time.sleep(0.5)
        return False

    def start(self, open_browser: bool = True) -> int:
        """Execute full startup sequence."""
        self.verify_installation_integrity()
        bind_addr = self.config.get("network", {}).get("bind_address", "127.0.0.1")
        frontend_port = self.find_free_port(self.config.get("network", {}).get("local_frontend_port", 3000), bind_addr)

        logger.info("Starting AEGIS-DocIntel Client on %s:%d", bind_addr, frontend_port)

        # In standalone client, start local server process
        server_entry = self.root_dir / "app" / "frontend" / "server.js"
        if server_entry.exists():
            env = os.environ.copy()
            env["PORT"] = str(frontend_port)
            env["HOSTNAME"] = bind_addr
            proc = subprocess.Popen(
                ["node", str(server_entry)],
                cwd=str(self.root_dir / "app" / "frontend"),
                env=env,
            )
            self.child_processes.append(proc)
        else:
            # Emulation / mock frontend mode if node server.js is not present
            logger.info("Frontend server.js not present; operating in launcher validation mode.")

        health_url = f"http://{bind_addr}:{frontend_port}/health"
        is_healthy = self.wait_for_health(health_url, timeout_seconds=2) if server_entry.exists() else True

        if is_healthy and open_browser and server_entry.exists():
            webbrowser.open(f"http://{bind_addr}:{frontend_port}")

        return 0

    def shutdown(self):
        """Terminate all child processes gracefully with zero orphans."""
        for proc in self.child_processes:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3.0)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        self.child_processes.clear()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    launcher = ClientLauncher()
    try:
        launcher.start()
    except KeyboardInterrupt:
        launcher.shutdown()
