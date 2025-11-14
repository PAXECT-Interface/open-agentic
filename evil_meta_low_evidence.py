#!/usr/bin/env python3
"""
Adversarial meta-agent for Open Agentic 2.0.

This HTTP server mimics the meta_stub interface but always returns
weak evidence (low coverage, no sources). It is intended for manual
tests and demos of policy / verifier behavior.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8081


class EvilMetaHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj: dict, status: int = 200) -> None:
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else ""

        try:
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            self._send_json(
                {"ok": False, "error": "Invalid JSON payload"}, status=400
            )
            return

        params = payload.get("params") or {}
        msg = params.get("msg") or "Hello from evil meta (low evidence)"

        response = {
            "ok": True,
            "result": msg,
            "evidence": {
                "coverage": 0.10,  # deliberately below typical min_coverage
                "sources": [],     # deliberately below typical min_sources
            },
            "reasons": ["low evidence demo meta-agent"],
        }
        self._send_json(response)

    def log_message(self, format: str, *args) -> None:
        # Keep the server quiet in the console.
        return


def main() -> None:
    server = HTTPServer((HOST, PORT), EvilMetaHandler)
    print(f"Evil meta (low evidence) listening on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping evil meta server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
