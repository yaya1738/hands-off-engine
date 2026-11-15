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
import time
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

REPO_ROOT = Path(__file__).parent.parent
COORDINATION_FILE = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
WEBHOOK_PORT = 8888
WEBHOOK_HOST = "127.0.0.1"
MAX_WEBHOOK_BYTES = 8192


def read_webhook_message(headers, stream):
    """Parse bounded coordination data; sender fields are claims, not identity."""
    if headers.get("Transfer-Encoding") or headers.get("transfer-encoding"):
        return 400, None
    raw_length = headers.get("Content-Length") or headers.get("content-length")
    try:
        length = int(raw_length)
    except (TypeError, ValueError):
        return 400, None
    if length <= 0:
        return 400, None
    if length > MAX_WEBHOOK_BYTES:
        return 413, None
    try:
        message = json.loads(stream.read(length).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return 400, None
    if not isinstance(message, dict):
        return 400, None
    required = ("from", "to", "type", "message")
    if any(not isinstance(message.get(key), str) or not message[key].strip() for key in required):
        return 400, None
    if any(len(message[key]) > limit for key, limit in (("from", 100), ("to", 100), ("type", 100), ("message", 4000))):
        return 400, None
    if "timestamp" in message and not isinstance(message["timestamp"], str):
        return 400, None
    return 200, message

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
        """Handle incoming message from another agent"""
        if self.path == '/coordination/message':
            status, message = read_webhook_message(self.headers, self.rfile)
            if status != 200:
                self.send_response(status)
                self.end_headers()
                return

            if 'timestamp' not in message:
                message['timestamp'] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Untrusted inbound data is never committed or pushed automatically.
            with open(COORDINATION_FILE, 'a') as f:
                f.write(json.dumps(message) + '\\n')

            if self.message_callback:
                self.message_callback(message)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'received'}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Health check endpoint"""
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
        print(f"🌐 Webhook: http://localhost:{WEBHOOK_PORT}/coordination/message")
        print(f"💚 Health: http://localhost:{WEBHOOK_PORT}/health")
        print("\n" + "="*60)
        print("Service is running. Press Ctrl+C to stop.")
        print("="*60 + "\n")

        self.running = True

        # Start file watcher
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
