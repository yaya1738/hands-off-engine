#!/usr/bin/env python3
"""Read-only coordination service with fail-closed mutation boundaries.

Incoming coordination writes, Git commits/pushes, and dependency installation
are governed by FactoryAuthorityGateway and are not performed here.
"""
import json
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
COORDINATION_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
WEBHOOK_PORT = 8888


class CoordinationWebhook(BaseHTTPRequestHandler):
    message_callback = None

    def do_POST(self):
        if self.path != "/coordination/message":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(503)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "authority_required",
            "disabled": True,
            "authority": "FactoryAuthorityGateway",
        }).encode())

    def do_GET(self):
        if self.path == "/health":
            payload = {"status": "running", "service": "coordination",
                       "timestamp": datetime.utcnow().isoformat()}
        elif self.path == "/coordination/messages":
            messages = []
            if COORDINATION_FILE.exists():
                try:
                    lines = COORDINATION_FILE.read_text().splitlines()
                    messages = [json.loads(line) for line in lines[-10:]]
                except (OSError, ValueError):
                    messages = []
            payload = messages
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, format, *args):
        pass


class RealtimeCoordinationService:
    """Read-only coordination server; mutation requests fail closed."""

    def __init__(self):
        self.running = False
        self.webhook_server = None

    def on_new_message(self, message):
        print(f"[{message.get('timestamp', '?')}] NEW MESSAGE")

    def start(self):
        self.running = True
        self.webhook_server = HTTPServer(("", WEBHOOK_PORT), CoordinationWebhook)
        thread = threading.Thread(target=self.webhook_server.serve_forever, daemon=True)
        thread.start()
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        if self.webhook_server:
            self.webhook_server.shutdown()


if __name__ == "__main__":
    print("[FACTORY-AUTHORITY] coordination mutations are disabled; dependency installation is disabled")
    RealtimeCoordinationService().start()
