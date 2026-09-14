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
        self.approval_file = self.state_dir / "approval_queue.json"

    # ── queue operations ──

    def submit_command(self, action, target, payload=None, sync=False, priority=0, timeout=300, mode="DRYRUN"):
        if payload is None:
            payload = {}
        cmd_id = str(uuid.uuid4())
        cmd = {
            "id": cmd_id, "source": "ai:claude", "action": action, "target": target, "payload": payload,
            "mode": mode, "timestamp": datetime.now(timezone.utc).isoformat(), "priority": priority, "sync": sync,
            "timeout_seconds": timeout, "status": "pending", "result": None, "error": None, "completed_at": None,
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
                                    if data.get("id") == cmd_id and data.get("status") in ["completed", "failed", "awaiting_approval", "awaiting_executor"]:
                                        return {"id": cmd_id, "status": data.get("status"), "result": data.get("result"), "error": data.get("error")}
                                except Exception:
                                    pass
            except Exception:
                pass
            time.sleep(0.5)
        return {"id": cmd_id, "status": "timeout", "error": "Command did not complete in time"}

    # ── convenience methods ──

    def query(self, target, query, sync=True):
        return self.submit_command(action="query", target=target, payload={"query": query}, sync=sync)

    def status(self, sync=True):
        return self.submit_command(action="status", target="system", sync=sync)

    def pause(self):
        return self.submit_command(action="pause", target="system", sync=False, priority=10)

    def resume(self):
        return self.submit_command(action="resume", target="system", sync=False, priority=10)

    def execute(self, action, params, target="executor", sync=True, priority=5, mode="DRYRUN"):
        return self.submit_command(action="execute", target=target, payload={"action": action, "params": params}, sync=sync, priority=priority, mode=mode)

    def adjust(self, parameter, value, sync=False):
        return self.submit_command(action="adjust", target="system", payload={"parameter": parameter, "value": value}, sync=sync)

    # ── approval workflow ──

    def _load_approval_queue(self):
        if self.approval_file.exists():
            try:
                return json.loads(self.approval_file.read_text())
            except Exception:
                pass
        return {"pending": [], "approved": [], "rejected": []}

    def _save_approval_queue(self, data):
        self.approval_file.write_text(json.dumps(data, indent=2) + "\n")

    def list_pending_approval(self):
        q = self._load_approval_queue()
        return q.get("pending", [])

    def approve(self, command_id):
        """Approve a pending command so the listener can process it."""
        q = self._load_approval_queue()
        found = None
        for p in q.get("pending", []):
            if p.get("id") == command_id:
                found = p
                break
        if not found:
            return {"status": "not_found", "error": f"No pending approval for {command_id}"}

        # Grab queued_at from approval entry before removing it
        queued_at = None
        for p in q.get("pending", []):
            if p.get("id") == command_id:
                queued_at = p.get("queued_at")
                break

        entry = {"id": command_id, "approved_at": datetime.now(timezone.utc).isoformat()}
        q["approved"].append(entry)
        q["pending"] = [p for p in q["pending"] if p.get("id") != command_id]
        self._save_approval_queue(q)

        # Also stamp approval_status and queued_at on the original queued command
        self._stamp_command_approval(command_id, "approved", queued_at=queued_at)
        return {"status": "approved", "id": command_id}

    def reject(self, command_id):
        """Reject a pending command."""
        q = self._load_approval_queue()
        found = None
        for p in q.get("pending", []):
            if p.get("id") == command_id:
                found = p
                break
        if not found:
            return {"status": "not_found", "error": f"No pending approval for {command_id}"}

        entry = {"id": command_id, "rejected_at": datetime.now(timezone.utc).isoformat()}
        q["rejected"].append(entry)
        q["pending"] = [p for p in q["pending"] if p.get("id") != command_id]
        self._save_approval_queue(q)

        self._stamp_command_approval(command_id, "rejected")
        return {"status": "rejected", "id": command_id}

    def _stamp_command_approval(self, command_id, approval_status, queued_at=None):
        """Stamp approval_status onto the original command in the queue.

        On approval, resets queue status to 'pending' and carries queued_at
        forward so the executor can verify approval freshness.
        """
        if not self.queue_file.exists():
            return
        new_lines = []
        with open(self.queue_file, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        d = json.loads(line)
                        if d.get("id") == command_id:
                            d["approval_status"] = approval_status
                            if approval_status == "approved":
                                d["status"] = "pending"
                                if queued_at:
                                    d["queued_at"] = queued_at
                        new_lines.append(json.dumps(d) + "\n")
                    except Exception:
                        new_lines.append(line)
        with open(self.queue_file, "w") as f:
            f.writelines(new_lines)

    # ── results / queries ──

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
                        except Exception:
                            pass
        except Exception:
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
                        except Exception:
                            pass
        except Exception:
            pass
        return pending
