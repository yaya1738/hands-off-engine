#!/usr/bin/env python3
"""
Real-Time Agent Coordination Service

Provides instant bidirectional communication between AI agents.
Runs as a persistent service with webhook endpoints.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import os
import hmac
import ipaddress
import time
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit
try:
    from watchdog.events import FileSystemEventHandler
except ImportError:
    class FileSystemEventHandler:
        """Import-safe placeholder; service startup still requires watchdog."""

import subprocess

REPO_ROOT = Path(__file__).parent.parent
COORDINATION_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
WEBHOOK_HOST = "127.0.0.1"
WEBHOOK_PORT = 8888
MAX_WEBHOOK_BODY_BYTES = 64 * 1024
DEFAULT_ALLOWED_SENDERS = {
    "claude-code", "copilot", "chatgpt", "anyclaw",
    "factory", "openclaw", "grok",
}
FORBIDDEN_SENDERS = {"operator", "telegram", "system", "system_internal"}


def is_loopback_host(host):
    """Accept only localhost or literal loopback addresses."""
    if not isinstance(host, str):
        return False
    host = host.strip().lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_local_webhook_request(host_header, server_port):
    """Require a loopback Host header on the exact bound port."""
    try:
        parsed = urlsplit("//" + (host_header or ""))
        return (
            is_loopback_host(parsed.hostname or "")
            and parsed.port == server_port
        )
    except ValueError:
        return False


def webhook_authorized(auth_header, expected_token=None):
    """Fail closed unless a configured bearer token matches in constant time."""
    expected = expected_token if expected_token is not None else os.getenv("COORDINATION_WEBHOOK_TOKEN", "")
    if not expected or not isinstance(auth_header, str):
        return False
    scheme, separator, supplied = auth_header.partition(" ")
    return (
        bool(separator)
        and scheme.lower() == "bearer"
        and bool(supplied)
        and hmac.compare_digest(supplied.strip(), expected)
    )


def allowed_webhook_senders():
    configured = os.getenv("COORDINATION_ALLOWED_SENDERS")
    if configured is None:
        return set(DEFAULT_ALLOWED_SENDERS)
    return {item.strip() for item in configured.split(",") if item.strip()} - FORBIDDEN_SENDERS


def validate_webhook_message(message):
    """Validate a small, typed, known-agent message; never accept operator identity."""
    if not isinstance(message, dict):
        return False, "message must be an object"
    required = ("from", "to", "type", "message")
    if any(not isinstance(message.get(key), str) or not message[key].strip() for key in required):
        return False, "required fields must be non-empty strings"
    sender = message["from"].strip()
    if sender in FORBIDDEN_SENDERS or sender not in allowed_webhook_senders():
        return False, "sender is not allowlisted"
    if len(message["message"]) > 20000:
        return False, "message exceeds size limit"
    return True, None

class CoordinationFileWatcher(FileSystemEventHandler):
    """Watches coordination file for new messages"""

    def __init__(self, callback):
        self.callback = callback
        self.last_position = 0

        # Initialize with current file size
        if COORDINATION_FILE.exists():
            with open(COORDINATION_FILE, 'r') as f:
                f.seek(0, 2)  # Seek to end
                self.last_position = f.tell()

    def on_modified(self, event):
        if event.src_path == str(COORDINATION_FILE):
            self.check_new_messages()

    def check_new_messages(self):
        """Read new messages since last check"""
        if not COORDINATION_FILE.exists():
            return

        with open(COORDINATION_FILE, 'r') as f:
            f.seek(self.last_position)
            new_content = f.read()
            self.last_position = f.tell()

            if new_content.strip():
                lines = new_content.strip().split('\n')
                for line in lines:
                    try:
                        message = json.loads(line)
                        self.callback(message)
                    except json.JSONDecodeError:
                        pass

class CoordinationWebhook(BaseHTTPRequestHandler):
    """Webhook endpoint for agents to POST messages"""

    message_callback = None

    def do_POST(self):
        """Handle an authenticated, allowlisted agent message."""
        if not is_local_webhook_request(
            self.headers.get("Host", ""), self.server.server_port
        ):
            self.send_response(403)
            self.end_headers()
            return
        if self.path != "/coordination/message":
            self.send_response(404)
            self.end_headers()
            return
        if not webhook_authorized(self.headers.get("Authorization")):
            code = 503 if not os.getenv("COORDINATION_WEBHOOK_TOKEN") else 401
            self.send_response(code)
            self.end_headers()
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_WEBHOOK_BODY_BYTES:
                self.send_response(413 if content_length > MAX_WEBHOOK_BODY_BYTES else 400)
                self.end_headers()
                return
            post_data = self.rfile.read(content_length)
            message = json.loads(post_data.decode("utf-8"))
            valid, reason = validate_webhook_message(message)
            if not valid:
                self.send_response(403 if reason == "sender is not allowlisted" else 400)
                self.end_headers()
                return

            if "timestamp" not in message:
                message["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # Webhook input is untrusted. Persist the event only; a separate
            # governed workflow owns review and any repository mutation.
            with open(COORDINATION_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(message) + "\n")

            if self.message_callback:
                self.message_callback(message)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
        except Exception as e:
            print(f"Error processing message: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        """Read-only local health and message endpoints."""
        if not is_local_webhook_request(
            self.headers.get("Host", ""), self.server.server_port
        ):
            self.send_response(403)
            self.end_headers()
            return
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'running',
                'service': 'coordination',
                'timestamp': datetime.utcnow().isoformat()
            }).encode())
        elif self.path == '/coordination/messages':
            # Get recent messages
            messages = []
            if COORDINATION_FILE.exists():
                with open(COORDINATION_FILE, 'r') as f:
                    lines = f.readlines()
                    messages = [json.loads(line) for line in lines[-10:]]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(messages).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

class RealtimeCoordinationService:
    """Main coordination service"""

    def __init__(self):
        self.running = False
        self.webhook_server = None
        self.file_observer = None

    def on_new_message(self, message):
        """Handle new coordination message"""
        print(f"\n{'='*60}")
        print(f"[{message['timestamp']}] NEW MESSAGE")
        print(f"From: {message['from']} → To: {message['to']}")
        print(f"Type: {message['type']}")
        print(f"Message: {message['message'][:200]}{'...' if len(message['message']) > 200 else ''}")
        print(f"{'='*60}\n")

        # If message is to claude-code and from copilot, we could auto-respond
        # For now, just notify
        if message['to'] in ['claude-code', 'all'] and message['from'] == 'copilot':
            print("⚡ COPILOT RESPONDED - Check coordination file for details")

    def start(self):
        """Start the real-time coordination service"""
        print("🚀 Starting Real-Time Agent Coordination Service...")
        print(f"📁 Watching: {COORDINATION_FILE}")
        print(f"🌐 Local webhook: http://{WEBHOOK_HOST}:{WEBHOOK_PORT}/coordination/message")
        if not os.getenv("COORDINATION_WEBHOOK_TOKEN"):
            print("🔒 POST disabled: set COORDINATION_WEBHOOK_TOKEN to enable authenticated agent ingress")
        print(f"💚 Health: http://localhost:{WEBHOOK_PORT}/health")
        print("\n" + "="*60)
        print("Service is running. Press Ctrl+C to stop.")
        print("="*60 + "\n")

        self.running = True

        # Start file watcher only after imports are resolved. This keeps the
        # webhook policy helpers importable in minimal test environments.
        from watchdog.observers import Observer
        event_handler = CoordinationFileWatcher(self.on_new_message)
        self.file_observer = Observer()
        self.file_observer.schedule(
            event_handler,
            str(COORDINATION_FILE.parent),
            recursive=False
        )
        self.file_observer.start()

        # Start webhook server
        CoordinationWebhook.message_callback = self.on_new_message
        self.webhook_server = HTTPServer((WEBHOOK_HOST, WEBHOOK_PORT), CoordinationWebhook)

        # Run webhook in thread
        webhook_thread = threading.Thread(
            target=self.webhook_server.serve_forever
        )
        webhook_thread.daemon = True
        webhook_thread.start()

        print("✅ Service started successfully!\n")

        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping service...")
            self.stop()

    def stop(self):
        """Stop the service"""
        self.running = False
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        if self.webhook_server:
            self.webhook_server.shutdown()
        print("✅ Service stopped")

if __name__ == '__main__':
    import sys

    # Check if watchdog is installed
    try:
        import watchdog
    except ImportError:
        print("Installing required dependency: watchdog...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'watchdog'])
        print("✅ Dependency installed. Please run again.")
        sys.exit(0)

    service = RealtimeCoordinationService()
    service.start()
