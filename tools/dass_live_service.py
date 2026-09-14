#!/usr/bin/env python3
"""Portable continuous DASS runtime for hosts outside GitHub Actions."""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tools.autonomous_integrated_supervisor import main as run_cycle

ROOT = Path(__file__).resolve().parents[1]
PORT = 10000
CYCLE_SECONDS = 300


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {}


def snapshot() -> dict:
    liveness = _read_json(ROOT / "state" / "autonomy_liveness.json")
    phase = _read_json(ROOT / "state" / "dass_phase.json")
    attestation = liveness.get("live_attestation")
    now = datetime.now(timezone.utc)
    fresh = False
    if isinstance(attestation, dict) and attestation.get("active") is True:
        try:
            observed = datetime.fromisoformat(str(attestation["observed_at"]).replace("Z", "+00:00"))
            expiry = datetime.fromtimestamp(float(attestation["expires_at"]), tz=timezone.utc)
            fresh = observed <= now <= expiry
        except (KeyError, TypeError, ValueError, OverflowError):
            fresh = False
    return {
        "service": "dass-portable-live-runtime",
        "observed_at": now.isoformat(),
        "live_system_active": liveness.get("live_system_active") is True,
        "operating_state": liveness.get("operating_state"),
        "converged": liveness.get("converged") is True,
        "execution_succeeded": liveness.get("execution_succeeded") is True,
        "attestation_fresh": fresh,
        "dass_achieved": phase.get("dass_achieved") is True and fresh and liveness.get("live_system_active") is True,
        "dass_phase": phase.get("phase"),
        "last_known_cycle_timestamp": liveness.get("last_known_cycle_timestamp"),
        "live_attestation": attestation,
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/health", "/dass"):
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(snapshot(), sort_keys=True).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def cycle_loop() -> None:
    while True:
        started = time.monotonic()
        try:
            run_cycle()
        except Exception as exc:
            print(json.dumps({"service": "dass-portable-live-runtime", "cycle_error": str(exc)}, sort_keys=True), flush=True)
        elapsed = time.monotonic() - started
        time.sleep(max(1, CYCLE_SECONDS - elapsed))


def main() -> None:
    threading.Thread(target=cycle_loop, daemon=True, name="dass-cycle").start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(json.dumps({"service": "dass-portable-live-runtime", "port": PORT, "cycle_seconds": CYCLE_SECONDS}, sort_keys=True), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
