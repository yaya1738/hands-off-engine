#!/usr/bin/env python3
"""Legacy autopilot control surface.

This listener is retained only as a compatibility/status endpoint. It is not
an execution authority. Historical `/run/*` endpoints could execute arbitrary
shell commands outside the Factory authority boundary and are intentionally
blocked.
"""

import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST, PORT = "127.0.0.1", 8765
TOKEN = os.environ.get("CONTROL_TOKEN", "")


class H(BaseHTTPRequestHandler):
    def _ok(self, body, code=200, ctype="text/plain; charset=utf-8"):
        if isinstance(body, (bytes, bytearray)):
            payload = body
        elif isinstance(body, str):
            payload = body.encode()
        else:
            payload = json.dumps(body).encode()
            ctype = "application/json; charset=utf-8"
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(payload)

    def _auth(self):
        return bool(TOKEN) and self.headers.get("X-Token", "") == TOKEN

    def _authorized(self):
        if self._auth():
            return True
        self._ok("unauthorized", 401)
        return False

    def do_POST(self):
        if not self._authorized():
            return
        path = self.path.split("?", 1)[0]
        if path.startswith("/run/"):
            return self._ok(
                {
                    "status": "BLOCKED",
                    "reason": "legacy_remote_execution_disabled",
                    "authority": "FactoryAuthorityGateway",
                },
                403,
                "application/json; charset=utf-8",
            )
        return self._ok("not found", 404)

    def do_GET(self):
        if not self._authorized():
            return
        path, _, qs = self.path.partition("?")
        query = dict(urllib.parse.parse_qsl(qs))

        if path == "/ping":
            return self._ok("pong")

        if path.startswith("/run/"):
            return self._ok(
                {
                    "status": "BLOCKED",
                    "reason": "legacy_remote_execution_disabled",
                    "authority": "FactoryAuthorityGateway",
                },
                403,
                "application/json; charset=utf-8",
            )

        if path == "/set/threshold":
            # Preserve informational compatibility without mutating runtime state.
            return self._ok(
                {
                    "status": "BLOCKED",
                    "reason": "legacy_remote_mutation_disabled",
                    "requested": query.get("v", "0.05"),
                    "authority": "FactoryAuthorityGateway",
                },
                403,
                "application/json; charset=utf-8",
            )

        return self._ok("not found", 404)


if __name__ == "__main__":
    print(f"Listening on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
