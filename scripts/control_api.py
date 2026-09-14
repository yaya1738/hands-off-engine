import json, uuid, time
from pathlib import Path
from datetime import datetime, timezone

class SystemControl:
    def __init__(self, repo_root=None):
        if repo_root is None:
            repo_root = Path.home() / "hands-off-engine"
        self.repo_root = repo_root
        self.state_dir = repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.state_dir / "command_queue.jsonl"
        self.results_file = self.state_dir / "results.jsonl"
    
    def submit_command(self, action, target, payload=None, sync=False, priority=0, timeout=300):
        if payload is None:
            payload = {}
        cmd_id = str(uuid.uuid4())
        cmd = {
            "id": cmd_id, "source": "ai:claude", "action": action, "target": target, "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(), "priority": priority, "sync": sync,
            "timeout_seconds": timeout, "status": "pending", "result": None, "error": None, "completed_at": None
        }
        try:
            with open(self.queue_file, "a") as f:
                f.write(json.dumps(cmd) + "\n")
        except Exception as e:
            raise RuntimeError(f"Failed to submit: {e}")
        if sync:
            return self._wait_for_result(cmd_id, timeout)
        return cmd_id
    
    def _wait_for_result(self, cmd_id, timeout):
        start = time.time()
        while time.time() - start < timeout:
            try:
                if self.queue_file.exists():
                    with open(self.queue_file, "r") as f:
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if data.get("id") == cmd_id and data.get("status") in ["completed", "failed"]:
                                        return {"id": cmd_id, "status": data.get("status"), "result": data.get("result"), "error": data.get("error")}
                                except:
                                    pass
            except:
                pass
            time.sleep(0.5)
        return {"id": cmd_id, "status": "timeout", "error": "Command did not complete in time"}
    
    def query(self, target, query, sync=True):
        return self.submit_command(action="query", target=target, payload={"query": query}, sync=sync)
    
    def status(self, sync=True):
        return self.submit_command(action="status", target="system", sync=sync)
    
    def pause(self):
        return self.submit_command(action="pause", target="system", sync=False, priority=10)
    
    def resume(self):
        return self.submit_command(action="resume", target="system", sync=False, priority=10)
    
    def execute(self, action, params, target="executor", sync=True, priority=5):
        return self.submit_command(action="execute", target=target, payload={"action": action, "params": params}, sync=sync, priority=priority)
    
    def adjust(self, parameter, value, sync=False):
        return self.submit_command(action="adjust", target="system", payload={"parameter": parameter, "value": value}, sync=sync)
    
    def get_results(self, since=None):
        if not self.results_file.exists():
            return []
        results = []
        try:
            with open(self.results_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if since is None or data.get("timestamp", "") >= since:
                                results.append(data)
                        except:
                            pass
        except:
            pass
        return results
    
    def get_pending_commands(self):
        if not self.queue_file.exists():
            return []
        pending = []
        try:
            with open(self.queue_file, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("status") == "pending":
                                pending.append(data)
                        except:
                            pass
        except:
            pass
        return pending
