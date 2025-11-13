#!/usr/bin/env python3
"""
Meta HTTP stub for Open Agentic 2.0.

This is a tiny HTTP JSON server used for local testing of the MetaHTTP plugin.

- Listens by default on 127.0.0.1:8081
- Accepts POST requests with JSON bodies:
    {"op": "<operation>", "params": {...}}
- Returns JSON:
    {
        "ok": bool,
        "result": any,
        "evidence": {"coverage": float, "sources": [...]},
        "reasons": [str, ...]
    }

This is only a demo/stub and not meant to access the open internet.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple


Output = Dict[str, Any]


def _error(reason: str) -> Output:
    return {
        "ok": False,
        "result": None,
        "evidence": None,
        "reasons": [reason],
    }


def _ok(result: Any, sources=None, coverage: float = 0.80) -> Output:
    if sources is None:
        sources = ["meta"]
    return {
        "ok": True,
        "result": result,
        "evidence": {
            "coverage": float(coverage),
            "sources": list(sources),
        },
        "reasons": [],
    }


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_echo(params: Dict[str, Any]) -> Output:
    """
    Echo operation for demos and tests.
    """
    msg = str(params.get("msg", "") or "")
    if not msg:
        return _error("empty msg")
    return _ok(msg, sources=["meta", "echo"], coverage=0.85)


def handle_extract(params: Dict[str, Any]) -> Output:
    """
    Fake 'extract' operation: in a real system this would extract
    structured data from a document. Here we just wrap the input.
    """
    url = str(params.get("url", "") or "")
    fields = params.get("fields") or []
    result = {
        "url": url,
        "fields": fields,
        "note": "meta_stub does not fetch real URLs; this is a local demo.",
    }
    return _ok(result, sources=["meta", "extract"], coverage=0.85)


def handle_health(params: Dict[str, Any]) -> Output:
    """
    Health-check endpoint.
    """
    return _ok(
        {"status": "ok", "info": "meta_stub alive"},
        sources=["meta", "health"],
        coverage=1.0,
    )


HANDLERS = {
    "echo": handle_echo,
    "extract": handle_extract,
    "health": handle_health,
}


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------


class MetaStubHandler(BaseHTTPRequestHandler):
    server_version = "MetaStub/0.1"

    def _send_json(self, status: int, payload: Output) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, _error("invalid JSON body"))
            return

        op = str(data.get("op") or data.get("operation") or "").strip()
        params = data.get("params") or {}

        if not op:
            self._send_json(400, _error("missing op"))
            return

        if not isinstance(params, dict):
            self._send_json(400, _error("params must be an object"))
            return

        handler = HANDLERS.get(op)
        if handler is None:
            self._send_json(400, _error(f"unknown op: {op}"))
            return

        try:
            out = handler(params)
        except Exception:
            # Fail safe: do not leak stack traces in the response.
            self._send_json(500, _error("internal error"))
            return

        self._send_json(200, out)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep output quiet by default; override if you want verbose logs.
        return


def run_server(host: str = "127.0.0.1", port: int = 8081) -> Tuple[str, int]:
    server_address = (host, port)
    httpd = HTTPServer(server_address, MetaStubHandler)
    print(f"Meta stub listening on http://{host}:{port}")
    httpd.serve_forever()
    return host, port


if __name__ == "__main__":
    run_server()
