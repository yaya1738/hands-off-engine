#!/usr/bin/env python3
import sys, json, time, uuid, threading
from pathlib import Path
from datetime import datetime, timezone

class AIAdapter:
    def __init__(self, system_name, repo_root=None):
        if repo_root is None:
            repo_root = Path.home() / "hands-off-engine"
        self.system_name = system_name
        self.repo_root = repo_root
        self.state_dir = repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.state_dir / "command_queue.jsonl"
        self.results_file = self.state_dir / "results.jsonl"
        self.adapter_log = self.state_dir / f"adapter_{system_name}.log"
    
    def log(self, msg, level="INFO"):
        ts = datetime.now(timezone.utc).isoformat()
        line = f"[{ts}] [{level}] [{self.system_name}] {msg}"
        print(line)
        try:
            with open(self.adapter_log, "a") as f:
                f.write(line + "\n")
        except:
            pass
    
    def get_pending_commands(self):
        if not self.queue_file.exists():
            return []
        commands = []
        try:
            with open(self.queue_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("target_system") == self.system_name and data.get("status") == "pending":
                                commands.append(data)
                        except:
                            pass
        except:
            pass
        return commands
    
    def process_command(self, cmd):
        return {"id": cmd.get("id"), "status": "completed", "result": {"message": f"Command received by {self.system_name}"}}
    
    def write_result(self, result):
        try:
            with open(self.results_file, "a") as f:
                f.write(json.dumps({"id": result.get("id"), "status": result.get("status"), "result": result.get("result"), "timestamp": datetime.now(timezone.utc).isoformat(), "source_system": self.system_name}) + "\n")
        except:
            pass
    
    def update_command_status(self, cmd_id, status):
        if not self.queue_file.exists():
            return
        try:
            lines = []
            with open(self.queue_file, "r") as f:
                lines = f.readlines()
            with open(self.queue_file, "w") as f:
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("id") == cmd_id:
                                data["status"] = status
                            f.write(json.dumps(data) + "\n")
                        except:
                            f.write(line)
        except:
            pass
    
    def run(self):
        self.log("Adapter started")
        while True:
            try:
                commands = self.get_pending_commands()
                if commands:
                    self.log(f"Found {len(commands)} commands")
                for cmd in commands:
                    cmd_id = cmd.get("id")
                    self.update_command_status(cmd_id, "executing")
                    try:
                        result = self.process_command(cmd)
                        self.write_result(result)
                        self.log(f"Processed: {cmd_id[:8]}...")
                    except Exception as e:
                        self.log(f"Error: {e}", "ERROR")
                        self.write_result({"id": cmd_id, "status": "failed", "result": {"error": str(e)}})
                time.sleep(5)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error: {e}", "ERROR")
                time.sleep(10)

class GrokAdapter(AIAdapter):
    def process_command(self, cmd):
        action = cmd.get("action")
        payload = cmd.get("payload", {})
        if action == "query":
            return {"id": cmd.get("id"), "status": "completed", "result": {"system": "Grok", "query": payload.get("query"), "response": f"Grok analysis: {payload.get('query', '')[:50]}...", "confidence": 0.85}}
        return {"id": cmd.get("id"), "status": "completed", "result": {"system": "Grok", "message": f"Grok received {action}"}}

class ChatGPTAdapter(AIAdapter):
    def process_command(self, cmd):
        action = cmd.get("action")
        payload = cmd.get("payload", {})
        if action == "query":
            return {"id": cmd.get("id"), "status": "completed", "result": {"system": "ChatGPT", "query": payload.get("query"), "response": f"ChatGPT analysis: {payload.get('query', '')[:50]}...", "confidence": 0.82}}
        return {"id": cmd.get("id"), "status": "completed", "result": {"system": "ChatGPT", "message": f"ChatGPT received {action}"}}

class OpenClawAdapter(AIAdapter):
    """OpenClaw adapter reconciled with canonical CommHub/messages.jsonl bus.

    Reads task_assignments from messages.jsonl via CommHub party routing.
    Writes results back to messages.jsonl. No separate queue.
    """

    def __init__(self, system_name="openclaw", repo_root=None):
        super().__init__(system_name, repo_root)
        self.coord_file = self.repo_root / "ai" / "coordination" / "messages.jsonl"
        self.inbound_file = self.state_dir / "inbound" / "openclaw.jsonl"

    def get_pending_commands(self):
        """Read task_assignments addressed to openclaw from the canonical bus."""
        commands = []
        # First check event router's inbound queue (from router)
        if self.inbound_file.exists():
            try:
                with open(self.inbound_file, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if data.get("routed"):
                                    commands.append({
                                        "id": data.get("event_id", ""),
                                        "action": "task_assignment",
                                        "payload": data,
                                        "source": "event_router",
                                    })
                            except json.JSONDecodeError:
                                pass
            except Exception:
                pass

        # Also scan messages.jsonl for task_assignments to openclaw
        if self.coord_file.exists():
            try:
                with open(self.coord_file, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                msg = json.loads(line)
                                if (msg.get("type") == "task_assignment" and
                                    msg.get("to") in ("openclaw", "all")):
                                    commands.append({
                                        "id": msg.get("msg_id", ""),
                                        "action": msg.get("context", {}).get("action", "unknown"),
                                        "payload": msg,
                                        "source": "coordination_bus",
                                    })
                            except json.JSONDecodeError:
                                pass
            except Exception:
                pass

        return commands

    def process_command(self, cmd):
        action = cmd.get("action")
        payload = cmd.get("payload", {})
        if action == "execute":
            return {"id": cmd.get("id"), "status": "completed", "result": {"system": "OpenClaw", "message": "OpenClaw executed", "execution_time_ms": 150, "success": True, "confidence": 0.88}}
        return {"id": cmd.get("id"), "status": "completed", "result": {"system": "OpenClaw", "message": f"OpenClaw received {action}"}}

    def write_result(self, result):
        """Write result back to canonical messages.jsonl via CommHub."""
        try:
            from scripts.comm_hub import CommHub
            hub = CommHub(repo_root=self.repo_root)
            hub.send("factory", "task_result", {
                "source": "openclaw",
                "id": result.get("id"),
                "status": result.get("status"),
                "result": result.get("result"),
            })
        except Exception as e:
            # Fallback: write to coordination bus directly
            try:
                msg = {
                    "from": "openclaw",
                    "to": "factory",
                    "type": "task_result",
                    "msg_id": result.get("id", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "context": {
                        "task_id": result.get("id", "unknown"),
                        "status": result.get("status"),
                        "result": result.get("result"),
                    },
                }
                with open(self.coord_file, "a") as f:
                    f.write(json.dumps(msg) + "\n")
            except Exception:
                self.log(f"Failed to write result: {e}", "ERROR")

def main():
    repo_root = Path.home() / "hands-off-engine"
    adapters = [GrokAdapter("grok", repo_root), ChatGPTAdapter("chatgpt", repo_root), OpenClawAdapter("openclaw", repo_root)]
    print("="*70)
    print("STARTING UNIVERSAL AI ADAPTERS: Grok, ChatGPT, OpenClaw")
    print("="*70)
    threads = []
    for adapter in adapters:
        t = threading.Thread(target=adapter.run, daemon=True)
        t.start()
        threads.append(t)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
