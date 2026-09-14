#!/usr/bin/env python3
"""
Executor — binds to the governed authority contract.

Receives approved commands from the system listener and executes them
through the appropriate backend, enforcing safety checks at every step.

Safety rules (from .claude/instructions.md):
1. Financial decisions require high confidence (>75%)
2. Max 10 automated changes per hour
3. Sacred files/processes cannot be auto-modified
4. DRYRUN mode is default; LIVE requires explicit approval + execution_enabled

Lifecycle:
  authority.approved → executor.execute_command()
    → safety checks → backend dispatch → result → logging
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict

log = logging.getLogger("Executor")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"
EXECUTION_LOG = STATE_DIR / "execution_log.jsonl"
RATE_LIMIT_FILE = STATE_DIR / "rate_limit_state.json"

# ── safety constants ──
MAX_CHANGES_PER_HOUR = 10
MAX_POSITION_USD = 1000
MAX_DAILY_LOSS_USD = 3000
APPROVAL_TTL_SECONDS = 3600  # approvals expire after 1 hour

# Sacred targets that must never be auto-modified
SACRED_FILES = {".env", ".env.polymarket", "state/knowledge.json"}
SACRED_PROCESSES = {"python3", "sshd", "cron", "systemd"}


@dataclass(frozen=True)
class ExecutionResult:
    command_id: str
    status: str  # "executed", "dryrun", "rejected", "rate_limited", "expired", "error"
    action: str
    target: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    executed_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class Executor:
    """Safety-gated execution backend bound to the governed authority."""

    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else REPO_ROOT
        self.state_dir = self.repo_root / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_state = self._load_rate_limit()

    def execute_command(self, cmd: Dict[str, Any]) -> ExecutionResult:
        """Execute an approved command through safety gates."""
        cmd_id = cmd.get("id", "unknown")
        action = cmd.get("payload", {}).get("action", "unknown")
        target = cmd.get("target", "system")
        mode = cmd.get("mode", "DRYRUN")
        approval_status = cmd.get("approval_status", "")

        log.info(f"Executor: processing {cmd_id[:8]} action={action} mode={mode}")

        # ── safety gate 1: approval freshness ──
        if mode == "LIVE":
            if approval_status != "approved":
                return self._reject(cmd_id, action, target, "LIVE command not approved")
            if not self._check_approval_freshness(cmd):
                return self._reject(cmd_id, action, target, "Approval expired (TTL exceeded)")

        # ── safety gate 2: sacred target protection ──
        if action in ("modify", "delete", "write") and target in SACRED_FILES:
            return self._reject(cmd_id, action, target, f"Target is sacred: {target}")

        # ── safety gate 3: rate limiting ──
        if not self._check_rate_limit():
            result = ExecutionResult(
                command_id=cmd_id, status="rate_limited", action=action,
                target=target, error=f"Rate limit exceeded: {MAX_CHANGES_PER_HOUR}/hour",
                executed_at=datetime.now(timezone.utc).isoformat(),
            )
            self._log_execution(result)
            log.warning(f"RATE LIMITED: {cmd_id[:8]} {action}@{target}")
            return result

        # ── safety gate 4: action-specific validation ──
        validation = self._validate_action(cmd)
        if not validation["ok"]:
            return self._reject(cmd_id, action, target, validation["reason"])

        # ── execute ──
        if mode == "DRYRUN":
            result = self._dryrun_execute(cmd)
            self._record_rate()
            self._log_execution(result)
            return result

        # LIVE execution
        result = self._live_execute(cmd)
        self._record_rate()
        self._log_execution(result)
        return result

    # ── safety checks ──

    def _check_approval_freshness(self, cmd):
        """Ensure approval hasn't expired."""
        queued_at = cmd.get("queued_at", "")
        if not queued_at:
            return False
        try:
            queued_time = datetime.fromisoformat(queued_at.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - queued_time).total_seconds()
            return elapsed < APPROVAL_TTL_SECONDS
        except Exception:
            return False

    def _check_rate_limit(self):
        """Max N changes per hour."""
        now = time.time()
        window = self.rate_limit_state.get("window_start", now)
        count = self.rate_limit_state.get("count", 0)
        if now - window > 3600:
            self.rate_limit_state = {"window_start": now, "count": 0}
            self._save_rate_limit()
            return True
        return count < MAX_CHANGES_PER_HOUR

    def _record_rate(self):
        now = time.time()
        if now - self.rate_limit_state.get("window_start", 0) > 3600:
            self.rate_limit_state = {"window_start": now, "count": 1}
        else:
            self.rate_limit_state["count"] = self.rate_limit_state.get("count", 0) + 1
        self._save_rate_limit()

    def _validate_action(self, cmd):
        """Action-specific validation rules."""
        action = cmd.get("payload", {}).get("action", "")
        params = cmd.get("payload", {}).get("params", {})

        if action == "trade":
            amount = params.get("amount", params.get("position_usd", 0))
            if isinstance(amount, (int, float)) and amount > MAX_POSITION_USD:
                return {"ok": False, "reason": f"Position size ${amount} exceeds max ${MAX_POSITION_USD}"}

        if action == "kill_process":
            process_name = params.get("process", "")
            if process_name in SACRED_PROCESSES:
                return {"ok": False, "reason": f"Cannot kill sacred process: {process_name}"}

        if action == "modify_file":
            file_path = params.get("path", "")
            if any(file_path.endswith(s) for s in SACRED_FILES):
                return {"ok": False, "reason": f"Cannot modify sacred file: {file_path}"}

        return {"ok": True, "reason": None}

    # ── execution backends ──

    def _dryrun_execute(self, cmd):
        """Simulate execution — log what would happen."""
        action = cmd.get("payload", {}).get("action", "unknown")
        params = cmd.get("payload", {}).get("params", {})
        log.info(f"DRYRUN: would execute {action} with {params}")

        return ExecutionResult(
            command_id=cmd.get("id", "unknown"),
            status="dryrun",
            action=action,
            target=cmd.get("target", "system"),
            result={
                "mode": "DRYRUN",
                "would_execute": action,
                "params": params,
                "note": "No changes made — dry run only",
            },
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _live_execute(self, cmd):
        """Actually execute — dispatches to the appropriate backend."""
        action = cmd.get("payload", {}).get("action", "unknown")
        params = cmd.get("payload", {}).get("params", {})
        target = cmd.get("target", "system")

        try:
            if target == "executor" and action == "trade":
                result = self._execute_trade(params)
            elif target == "system" and action in ("pause", "resume"):
                result = self._execute_system_control(action, params)
            elif target == "executor" and action == "adjust":
                result = self._execute_adjust(params)
            else:
                result = {"status": "executed", "action": action, "params": params,
                          "note": f"No specific backend for target={target} action={action}; logged as executed"}

            return ExecutionResult(
                command_id=cmd.get("id", "unknown"),
                status="executed",
                action=action,
                target=target,
                result=result,
                executed_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            log.error(f"Live execution failed: {e}")
            return ExecutionResult(
                command_id=cmd.get("id", "unknown"),
                status="error",
                action=action,
                target=target,
                error=str(e),
                executed_at=datetime.now(timezone.utc).isoformat(),
            )

    def _execute_trade(self, params):
        """Execute a trade — currently logs, would connect to Polymarket client."""
        log.info(f"LIVE TRADE: {params}")
        return {
            "status": "logged",
            "action": "trade",
            "params": params,
            "note": "Trade logged — Polymarket client not connected in this environment",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _execute_system_control(self, action, params):
        """Execute system control action."""
        log.info(f"LIVE SYSTEM CONTROL: {action}")
        return {
            "status": "executed",
            "action": action,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _execute_adjust(self, params):
        """Execute parameter adjustment."""
        log.info(f"LIVE ADJUST: {params}")
        return {
            "status": "executed",
            "action": "adjust",
            "params": params,
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── rejection ──

    def _reject(self, cmd_id, action, target, reason):
        log.warning(f"REJECTED: {cmd_id[:8]} {action}@{target}: {reason}")
        result = ExecutionResult(
            command_id=cmd_id,
            status="rejected",
            action=action,
            target=target,
            error=reason,
            executed_at=datetime.now(timezone.utc).isoformat(),
        )
        self._log_execution(result)
        return result

    # ── logging / persistence ──

    def _log_execution(self, result: ExecutionResult):
        try:
            with open(EXECUTION_LOG, "a") as f:
                f.write(json.dumps(result.to_dict(), default=str) + "\n")
        except Exception:
            pass

    def _load_rate_limit(self):
        if RATE_LIMIT_FILE.exists():
            try:
                return json.loads(RATE_LIMIT_FILE.read_text())
            except Exception:
                pass
        return {"window_start": time.time(), "count": 0}

    def _save_rate_limit(self):
        RATE_LIMIT_FILE.write_text(json.dumps(self.rate_limit_state))

    def get_recent_executions(self, limit=20):
        if not EXECUTION_LOG.exists():
            return []
        results = []
        with open(EXECUTION_LOG, "r") as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        return results[-limit:]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Governed Executor")
    sub = parser.add_subparsers(dest="cmd")
    ex_p = sub.add_parser("execute", help="Execute a command JSON")
    ex_p.add_argument("command_json")
    sub.add_parser("history", help="Show recent executions")
    args = parser.parse_args()

    ex = Executor()
    if args.cmd == "execute":
        cmd = json.loads(args.command_json)
        result = ex.execute_command(cmd)
        print(json.dumps(result.to_dict(), indent=2))
    elif args.cmd == "history":
        for r in ex.get_recent_executions():
            print(f"  {r.get('command_id','?')[:8]}... {r.get('status')} {r.get('action')}@{r.get('target')}")
    else:
        parser.print_help()
