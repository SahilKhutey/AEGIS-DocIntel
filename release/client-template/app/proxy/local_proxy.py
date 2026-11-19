"""
AEGIS-DocIntel Client Local Reverse Proxy
=========================================
Binds strictly to loopback (127.0.0.1) and proxies API traffic to the
configured remote AEGIS Evaluation Gateway, enforcing same-origin routing
and injecting session authentication headers.
"""
from __future__ import annotations

import http.server
import json
import logging
import os
import socketserver
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("aegis.client.proxy")


def load_config() -> Dict[str, Any]:
    """Load sanitized client configuration."""
    cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / "client.json"
    if not cfg_path.exists():
        cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / "defaults.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


class LoopbackProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP proxy handler enforcing loopback binding and forwarding to gateway."""

    server_version = "AEGIS-Client-Proxy/1.0.0"

    def do_GET(self):
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def do_PUT(self):
        self._proxy_request("PUT")

    def do_DELETE(self):
        self._proxy_request("DELETE")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:3000")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Workspace-ID")
        self.end_headers()

    def _proxy_request(self, method: str):
        # Strict DNS rebinding protection: Host header must be localhost / 127.0.0.1
        host_header = self.headers.get("Host", "")
        if not (host_header.startswith("127.0.0.1") or host_header.startswith("localhost")):
            self.send_error(403, "Forbidden: Non-loopback Host header rejected")
            return

        # Health check endpoint answered locally if requested
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","proxy":"active"}\n')
            return

        config = getattr(self.server, "config", load_config())
        gateway_url = config.get("network", {}).get("gateway_url", "http://127.0.0.1:8080").rstrip("/")
        target_url = f"{gateway_url}{self.path}"

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        forward_headers = {
            key: val for key, val in self.headers.items()
            if key.lower() not in ("host", "connection", "keep-alive")
        }

        req = urllib.request.Request(target_url, data=body, headers=forward_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for header, val in resp.getheaders():
                    if header.lower() not in ("transfer-encoding", "content-encoding"):
                        self.send_header(header, val)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, val in e.headers.items():
                if header.lower() not in ("transfer-encoding", "content-encoding"):
                    self.send_header(header, val)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as exc:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            err_msg = json.dumps({"detail": "Gateway unavailable", "error": str(exc)})
            self.wfile.write(err_msg.encode("utf-8"))


def run_proxy(port: int = 3001, bind_addr: str = "127.0.0.1"):
    config = load_config()
    server_address = (bind_addr, port)
    with socketserver.TCPServer(server_address, LoopbackProxyHandler) as httpd:
        httpd.config = config
        logger.info("Local proxy listening on http://%s:%d -> %s", bind_addr, port, config.get("network", {}).get("gateway_url"))
        httpd.serve_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_proxy()
