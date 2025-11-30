#!/usr/bin/env python3
"""
Master Orchestrator - Unified System Control
=============================================

This is the brain that coordinates ALL autonomous systems serving Yair Siegel.

Purpose:
- Unify Claude CLI, AI Nexus, Spark Plug, and all automation
- Ensure continuous operation aligned with user's goals
- Orchestrate across all AI agents and components
- Maintain system coherence and health

Design Philosophy:
- The system serves the user (Yair Siegel)
- Reduce user's workload
- Improve user's quality of life
- Operate autonomously without prompts
- Self-improve continuously

Invocation:
- Cron: Every 6 hours (after healthcheck)
- Manual: python3 scripts/master_orchestrator.py
- Triggered: By self-healing agent on critical issues
"""

import json
import sys
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional

# Setup
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("/var/log/hands-off/master_orchestrator.log"),
        logging.StreamHandler()
    ]
)
LOG = logging.getLogger(__name__)

# Core files
UNIFIED_STATE = REPO_ROOT / "state" / "UNIFIED_SYSTEM_STATE.json"
TASK_QUEUE = REPO_ROOT / "state" / "autonomous_task_queue.json"
COORDINATION = REPO_ROOT / "ai" / "coordination" / "messages.jsonl"
TRADING_MODE = REPO_ROOT / "state" / "trading_mode.json"
RISK_PROFILE = REPO_ROOT / "state" / "risk_profile.json"
HARD_LIMITS = REPO_ROOT / "config" / "hard_limits.json"
PERFORMANCE_LOG = REPO_ROOT / "logs" / "trading_performance.jsonl"


class MasterOrchestrator:
    """
    The Master Orchestrator unifies all autonomous systems.

    It serves as the central coordinator ensuring:
    1. All systems work toward user's goals
    2. No component operates in isolation
    3. System health is maintained
    4. User receives maximum benefit with minimum intervention
    """

    def __init__(self):
        self.state = self.load_unified_state()
        self.owner = self.state.get("owner", {})
        self.directive = self.state.get("core_directive", {})

    def load_unified_state(self) -> dict:
        """Load unified state, always syncing risk_profile from authoritative source."""
        if UNIFIED_STATE.exists():
            state = json.loads(UNIFIED_STATE.read_text())
        else:
            state = {}

        # Always sync risk_profile from authoritative source - never trust cached values
        self._sync_risk_profile_from_source(state)
        return state

    def _sync_risk_profile_from_source(self, state: dict):
        """Sync risk_profile in unified state from authoritative risk_profile.json."""
        if not RISK_PROFILE.exists():
            return

        authoritative = json.loads(RISK_PROFILE.read_text())

        # Ensure operational_state exists
        if "operational_state" not in state:
            state["operational_state"] = {}

        # Overwrite with authoritative values - this file is read-only cache, not source of truth
        state["operational_state"]["risk_profile"] = {
            "max_position_usd": authoritative.get("max_position_usd", 50),
            "max_daily_loss_usd": authoritative.get("max_daily_loss_usd", 200),
            "max_trades_per_hour": authoritative.get("max_trades_per_hour", 10),
            "confidence_threshold": authoritative.get("confidence_threshold", 0.45),
            "scale_factor": authoritative.get("scale_factor", 1.0),
            "_source": "synced from state/risk_profile.json - do not edit here"
        }

        # Save the synced state
        UNIFIED_STATE.write_text(json.dumps(state, indent=2))

    def save_unified_state(self):
        """Save the unified system state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        UNIFIED_STATE.write_text(json.dumps(self.state, indent=2))

    def run_orchestration_cycle(self) -> Dict:
        """
        Run a complete orchestration cycle.

        Steps:
        1. Check system health
        2. Assess goal progress
        3. Coordinate AI agents
        4. Queue necessary tasks
        5. Update state
        6. Notify if needed
        """
        LOG.info("=" * 60)
        LOG.info("MASTER ORCHESTRATION CYCLE")
        LOG.info(f"Serving: {self.owner.get('name', 'Unknown')}")
        LOG.info("=" * 60)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health_status": None,
            "goal_progress": None,
            "tasks_queued": [],
            "notifications": [],
            "actions_taken": []
        }

        # Step 1: System Health
        health_ok, health_issues = self.check_system_health()
        results["health_status"] = "healthy" if health_ok else f"issues: {health_issues}"

        if not health_ok:
            LOG.warning(f"Health issues detected: {health_issues}")
            self.trigger_self_healing(health_issues)
            results["actions_taken"].append("triggered_self_healing")

        # Step 2: Goal Progress
        progress = self.assess_goal_progress()
        results["goal_progress"] = progress

        # Step 3: Coordinate AI Agents
        agent_tasks = self.coordinate_ai_agents()
        results["tasks_queued"].extend(agent_tasks)

        # Step 4: Check for user-facing needs
        needs_attention = self.check_user_attention_needed()
        if needs_attention:
            self.send_telegram_summary(needs_attention)
            results["notifications"].append(needs_attention)

        # Step 5: Update state
        self.state["harmony_status"]["last_orchestration"] = datetime.now(timezone.utc).isoformat()
        self.save_unified_state()

        # Step 6: Log coordination message
        self.log_coordination({
            "type": "orchestration_complete",
            "results": results
        })

        LOG.info("=" * 60)
        LOG.info("ORCHESTRATION CYCLE COMPLETE")
        LOG.info("=" * 60)

        return results

    def check_system_health(self) -> Tuple[bool, List[str]]:
        """Check overall system health."""
        issues = []

        # Run healthcheck
        try:
            result = subprocess.run(
                ["./scripts/healthcheck.sh"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(REPO_ROOT)
            )
            if result.returncode != 0:
                issues.append("healthcheck_failed")
        except Exception as e:
            issues.append(f"healthcheck_error: {e}")

        # Check critical files
        critical_files = [TRADING_MODE, RISK_PROFILE, TASK_QUEUE]
        for f in critical_files:
            if not f.exists():
                issues.append(f"missing_{f.name}")
            else:
                try:
                    json.loads(f.read_text())
                except:
                    issues.append(f"corrupted_{f.name}")

        # Check cron is running
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "run_and_notify" not in result.stdout:
                issues.append("cron_missing")
        except:
            issues.append("cron_check_failed")

        return len(issues) == 0, issues

    def trigger_self_healing(self, issues: List[str]):
        """Trigger self-healing for detected issues."""
        try:
            subprocess.run(
                ["python3", str(REPO_ROOT / "scripts" / "self_healing_agent.py"), "--once"],
                capture_output=True,
                timeout=120,
                cwd=str(REPO_ROOT)
            )
            LOG.info("Self-healing triggered")
        except Exception as e:
            LOG.error(f"Self-healing failed: {e}")

    def assess_goal_progress(self) -> Dict:
        """Assess progress toward user's goals."""
        progress = {
            "profit_goal": 0,
            "automation_level": "high",
            "user_intervention_count": 0,
            "system_uptime": "99%+"
        }

        # Check trading performance
        if PERFORMANCE_LOG.exists():
            try:
                total_pnl = 0
                trade_count = 0
                with open(PERFORMANCE_LOG) as f:
                    for line in f:
                        entry = json.loads(line)
                        total_pnl += entry.get("realized_pnl_usd", 0)
                        trade_count += 1

                progress["total_pnl"] = total_pnl
                progress["trade_count"] = trade_count

                # Progress toward $15k goal
                target = self.state.get("financial_targets", {}).get("profit_goal_usd", 15000)
                progress["profit_goal_pct"] = (total_pnl / target * 100) if target > 0 else 0
            except:
                pass

        return progress

    def coordinate_ai_agents(self) -> List[str]:
        """Coordinate AI agents and queue tasks as needed."""
        tasks_queued = []

        # Check if Claude CLI needs tasks
        if TASK_QUEUE.exists():
            queue = json.loads(TASK_QUEUE.read_text())
            pending_count = len(queue.get("tasks", []))

            if pending_count == 0:
                # Queue a routine optimization task
                self.add_task({
                    "id": f"routine_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    "title": "Routine system optimization",
                    "description": "Review system state and implement any low-risk improvements",
                    "priority": "low",
                    "source": "master_orchestrator"
                })
                tasks_queued.append("routine_optimization")

        return tasks_queued

    def add_task(self, task: Dict):
        """Add a task to the autonomous task queue."""
        if TASK_QUEUE.exists():
            queue = json.loads(TASK_QUEUE.read_text())
        else:
            queue = {"tasks": [], "updated_at": None}

        task["created_at"] = datetime.now(timezone.utc).isoformat()
        queue["tasks"].append(task)
        queue["updated_at"] = datetime.now(timezone.utc).isoformat()

        TASK_QUEUE.write_text(json.dumps(queue, indent=2))

    def check_user_attention_needed(self) -> Optional[str]:
        """Check if user needs to be notified."""
        # Check for critical issues
        if not TRADING_MODE.exists():
            return "Trading mode file missing - system may need attention"

        mode = json.loads(TRADING_MODE.read_text())

        # Check if paused for too long
        if mode.get("auto_paused"):
            last_changed = mode.get("last_changed")
            if last_changed:
                changed_time = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
                hours_paused = (datetime.now(timezone.utc) - changed_time).total_seconds() / 3600
                if hours_paused > 24:
                    return f"Trading paused for {hours_paused:.0f} hours - review recommended"

        return None

    def send_telegram_summary(self, message: str):
        """Send summary to user via Telegram."""
        try:
            # Import notification module
            sys.path.insert(0, str(REPO_ROOT / "termux-hands-off" / "agent"))
            from notify import send_notification
            send_notification(f"[Orchestrator] {message}", "hands-off")
            LOG.info(f"Sent Telegram: {message}")
        except Exception as e:
            LOG.error(f"Failed to send Telegram: {e}")

    def log_coordination(self, data: Dict):
        """Log a coordination message."""
        COORDINATION.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "master_orchestrator",
            "to": "all",
            **data
        }

        with open(COORDINATION, "a") as f:
            f.write(json.dumps(entry) + "\n")


def main():
    """Run the master orchestrator."""
    orchestrator = MasterOrchestrator()

    # Check for specific commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "--status":
            state = orchestrator.load_unified_state()
            print(json.dumps(state, indent=2))
            return

        elif cmd == "--health":
            ok, issues = orchestrator.check_system_health()
            print(f"Health: {'OK' if ok else 'ISSUES'}")
            if issues:
                for issue in issues:
                    print(f"  - {issue}")
            return

    # Run full orchestration cycle
    results = orchestrator.run_orchestration_cycle()

    # Print summary
    print(f"\nOrchestration complete:")
    print(f"  Health: {results['health_status']}")
    print(f"  Tasks queued: {len(results['tasks_queued'])}")
    print(f"  Notifications: {len(results['notifications'])}")


if __name__ == "__main__":
    main()
