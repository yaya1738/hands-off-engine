#!/usr/bin/env python3
"""
Proactive Monitor — the autonomous system's eyes and ears.

Watches system state, market positions, and approval queues.
Pushes alerts through the CommHub when something needs attention.
Runs continuously as a long-lived process alongside governed_root.
"""

import json
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [ProactiveMonitor] %(message)s')
log = logging.getLogger("ProactiveMonitor")

REPO_ROOT = Path.home() / "hands-off-engine"
STATE_DIR = REPO_ROOT / "state"

# ── State files we watch ──
APPROVAL_FILE = STATE_DIR / "approval_queue.json"
ROOT_STATUS = STATE_DIR / "governed_root_status.json"
AUTONOMY_STATUS = STATE_DIR / "autonomy_status.json"
RESULTS_FILE = STATE_DIR / "results.jsonl"
MONITOR_STATE = STATE_DIR / "monitor_state.json"
COMM_LOG = STATE_DIR / "comm_log.jsonl"


class ProactiveMonitor:
    """Continuously watches system state and pushes proactive alerts."""

    def __init__(self):
        self.state = self._load_state()
        self.alert_cooldowns = {}  # alert_key -> last_sent_timestamp

    def _load_state(self):
        if MONITOR_STATE.exists():
            try:
                return json.loads(MONITOR_STATE.read_text())
            except Exception:
                pass
        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "cycles": 0,
            "alerts_sent": 0,
            "last_cycle": None,
        }

    def _save_state(self):
        MONITOR_STATE.write_text(json.dumps(self.state, indent=2, default=str) + "\n")

    def _can_alert(self, alert_key, cooldown_seconds=300):
        """Rate-limit alerts to avoid spam."""
        last = self.alert_cooldowns.get(alert_key, 0)
        now = time.time()
        if now - last < cooldown_seconds:
            return False
        self.alert_cooldowns[alert_key] = now
        return True

    # Only these alert types reach the operator. Everything else is logged silently.
    CRITICAL_ALERTS = {"approval_needed", "error", "trade_alert", "system_down"}

    def _send_alert(self, alert_type, payload, alert_key=None):
        """Send alert through CommHub — only CRITICAL alerts reach the operator."""
        if not self._can_alert(alert_key or alert_type):
            return False
        # Filter: only truly important things bother Yair
        severity = payload.get("severity", "normal")
        if severity != "critical" and alert_type not in self.CRITICAL_ALERTS:
            log.info(f"Alert suppressed (not critical): {alert_type}")
            return False
        try:
            from scripts.comm_hub import CommHub
            hub = CommHub()
            result = hub.send("operator", alert_type, payload, source="proactive_monitor")
            log.info(f"Alert sent: {alert_type} -> {result.get('status')}")
            self.state["alerts_sent"] = self.state.get("alerts_sent", 0) + 1
            return True
        except Exception as e:
            log.error(f"Failed to send alert: {e}")
            return False

    def check_approval_queue(self):
        """Check for pending approvals that need operator attention."""
        if not APPROVAL_FILE.exists():
            return []
        try:
            q = json.loads(APPROVAL_FILE.read_text())
            pending = q.get("pending", [])
            alerts = []
            for cmd in pending:
                cmd_id = cmd.get("id", "unknown")
                alert_key = f"approval_{cmd_id}"
                if self._can_alert(alert_key, cooldown_seconds=600):
                    payload = {
                        "title": "Approval Needed",
                        "command_id": cmd_id,
                        "action": cmd.get("payload", {}).get("action", "unknown"),
                        "mode": cmd.get("mode", "DRYRUN"),
                        "queued_at": cmd.get("queued_at", "unknown"),
                        "instruction": f"Reply with: /approve {cmd_id} or /reject {cmd_id}",
                    }
                    self._send_alert("approval_needed", payload, alert_key)
                    alerts.append(cmd_id)
            return alerts
        except Exception as e:
            log.error(f"Approval check failed: {e}")
            return []

    def check_governed_root(self):
        """Check if the governed root daemon is running."""
        if not ROOT_STATUS.exists():
            return self._send_alert("error", {
                "title": "Governed Root Missing",
                "instruction": "Run: python3 scripts/bootstrap.py",
            }, "governed_root_missing")

        try:
            status = json.loads(ROOT_STATUS.read_text())
            if status.get("status") != "running":
                return self._send_alert("error", {
                    "title": "Governed Root Down",
                    "status": status.get("status", "unknown"),
                    "instruction": "System may need manual restart",
                }, "governed_root_down")
        except Exception:
            return self._send_alert("error", {
                "title": "Governed Root Status Corrupt",
                "instruction": "Check state/governed_root_status.json",
            }, "governed_root_corrupt")
        return False

    def check_failed_commands(self):
        """Check for recently failed commands."""
        if not RESULTS_FILE.exists():
            return []
        try:
            failures = []
            with open(RESULTS_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        if r.get("status") == "failed":
                            failures.append(r)
            # Only alert on new failures
            recent = failures[-5:] if failures else []
            for f in recent:
                cmd_id = f.get("id", "unknown")
                alert_key = f"fail_{cmd_id}"
                error = f.get("result", {}).get("error", "unknown error")
                self._send_alert("error", {
                    "title": "Command Failed",
                    "command_id": cmd_id,
                    "error": error,
                }, alert_key)
            return recent
        except Exception as e:
            log.error(f"Failed command check error: {e}")
            return []

    def check_comm_log(self):
        """Check for inbound messages that need routing."""
        if not COMM_LOG.exists():
            return 0
        try:
            # Check last 10 entries for unhandled inbound messages
            with open(COMM_LOG, "r") as f:
                lines = f.readlines()
            count = 0
            for line in lines[-10:]:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("direction") == "inbound":
                        msg = entry.get("msg", {})
                        if msg.get("type") in ("trade_command", "execute_command"):
                            count += 1
            return count
        except Exception:
            return 0

    def generate_status_summary(self):
        """Generate a human-readable status summary."""
        parts = [
            f"🕐 Monitor Cycle #{self.state.get('cycles', 0)}",
            f"📊 Alerts sent: {self.state.get('alerts_sent', 0)}",
        ]

        # Goverend root status
        if ROOT_STATUS.exists():
            try:
                s = json.loads(ROOT_STATUS.read_text())
                parts.append(f"🟢 Root: {s.get('status', '?')} (authority={s.get('authority', '?')})")
            except Exception:
                parts.append("🔴 Root: status unknown")

        # Approval queue
        if APPROVAL_FILE.exists():
            try:
                q = json.loads(APPROVAL_FILE.read_text())
                pending = len(q.get("pending", []))
                if pending > 0:
                    parts.append(f"⏳ {pending} approval(s) pending")
                else:
                    parts.append("✅ No pending approvals")
            except Exception:
                pass

        # Recent failures
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE, "r") as f:
                    lines = f.readlines()
                failures = sum(1 for l in lines if '"failed"' in l)
                if failures > 0:
                    parts.append(f"⚠️ {failures} failed command(s)")
            except Exception:
                pass

        return "\n".join(parts)

    def run_cycle(self):
        """Run one monitoring cycle."""
        self.state["cycles"] = self.state.get("cycles", 0) + 1
        self.state["last_cycle"] = datetime.now(timezone.utc).isoformat()

        log.info(f"Monitor cycle #{self.state['cycles']}")

        # Run all checks
        approval_alerts = self.check_approval_queue()
        root_ok = self.check_governed_root()
        failed = self.check_failed_commands()
        inbound = self.check_comm_log()

        self._save_state()

        return {
            "cycle": self.state["cycles"],
            "approval_alerts": len(approval_alerts),
            "root_ok": not root_ok,
            "failures": len(failed),
            "inbound_pending": inbound,
        }

    def run(self, interval=30):
        """Run the monitor continuously."""
        log.info("=" * 60)
        log.info("PROACTIVE MONITOR STARTED")
        log.info(f"Interval: {interval}s")
        log.info(f"State: {MONITOR_STATE}")
        log.info("=" * 60)

        while True:
            try:
                result = self.run_cycle()
                if result["approval_alerts"] > 0 or result["failures"] > 0:
                    summary = self.generate_status_summary()
                    log.info(f"\n{summary}")
            except Exception as e:
                log.error(f"Monitor cycle error: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Proactive Monitor")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    parser.add_argument("--interval", type=int, default=30, help="Seconds between cycles")
    parser.add_argument("--status", action="store_true", help="Print status summary and exit")
    args = parser.parse_args()

    monitor = ProactiveMonitor()

    if args.status:
        print(monitor.generate_status_summary())
    elif args.once:
        result = monitor.run_cycle()
        print(json.dumps(result, indent=2))
        print(monitor.generate_status_summary())
    else:
        monitor.run(interval=args.interval)
